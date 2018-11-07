""" The base class for PEWPEW processing. See :doc:`usage`.
"""

from multiprocessing import Process, Queue, TimeoutError, Value
from multiprocessing.queues import Empty, Full
from abc import abstractmethod, ABCMeta
import logging
import copy


__default_exit_flag__ = Value('b', True)
__fmt__ = "%(levelname)s: %(asctime)s - %(name)s - %(process)s - %(message)s"


class StreamElement(Process):

    """ Subclass this abstract class for concrete implementation
    of pewpew processing
    """

    __metaclass__ = ABCMeta

    def __init__(self, exit_flag=None, inqueue=None, outqueue=None, **kwargs):
        """ The base constructor must always be called by the subclass.

        Parameters:
        ==========

        exit_flag: multiprocessing.Value
            A global exit flag. When set to `False`, will cause all
            threads to exit gracefully.

        inqueue: multiprocessing.Queue
            Data queue for incoming data.

        outqueue: multiprocessing.Queue
            Data queue for outgoing data.

        """
        super(StreamElement, self).__init__()
        self.inqueue = inqueue
        self.outqueue = outqueue
        self.config = kwargs

        self.fail_flag = exit_flag  # Signals False if failure has occurred
        if self.fail_flag is None:
            self.fail_flag = __default_exit_flag__
        self.input_flags = []  # Holds values from inputs to signal chain exit
        self.exit_flag = Value('b', True)  # For forwarding

        self.timeout = int(kwargs.get("timeout", 120))
        self.queuelen = int(kwargs.get("default_queuelen", 10))
        self.n_tries = int(kwargs.get("n_tries", 10))
        self.debug = bool(kwargs.get('debug', False))

    def signal_exit_on_failure(fn):
        """Helper decorator which sets appropriate flags when exceptions
        occur in daughter processes.
        """
        def wrapped(self=None, **kwargs):
            try:
                return fn(self, **kwargs)
            except Exception as e:
                self.log.info("signaling exit to all processes")
                self.log.warning(e)
                self.fail_flag.value = False
                raise e
        return wrapped

    def run(self):
        """Called by multiprocessing.Process.
        Executes main event loop for process.
        """
        self.event_loop()
        msg = "exiting with flags {} {}"
        self.log.debug(msg.format(self.fail_flag.value,
                                  self.exit_flag.value))

    def _log_(self):
        log = logging.getLogger(str(self.__class__).split('\'')[1])
        # formatter = logging.Formatter(__fmt__)
        return log

    @signal_exit_on_failure
    def get_data(self):
        """ Gets data from the input Queue.

        Returns
        =======

        A dict of pickle-able objects.
        """
        if not self.check_input_flags():
            self.log.debug("Inputs are finished. Setting timeout to 0.")
            self.timeout = 0
        if self.inqueue is not None:
            try:
                return self.inqueue.get(timeout=self.timeout)
            except (TimeoutError, Empty):
                if not self.check_input_flags():
                    self.exit_flag.value = False
                else:
                    self.fail_flag.value = False
                return None
        return {'data': {}, 'meta': {}}

    @signal_exit_on_failure
    def put_data(self, data):
        """ Attempts to put data on the queue for the next node.
        If the data is a list, then it puts the data on the queue
        one item at a time.

        Parameters:
        ===========

        data : list or dict
            The data to put on the queue.

        Note:
        =====

        This function must be called as `self.put_data(data={})`. Where
        the argument keyword must be used explicitely.

        """
        if not self.valid_data(data):
            msg = "cannot understand output data type: {}"
            self.log.warning(msg.format(type(data)))
            return

        if self.outqueue is not None:
            if isinstance(data, list):
                for i in data:
                    self.put_data(data=i)
            else:
                for try_ in range(self.n_tries):
                    success = False
                    try:
                        self.outqueue.put(copy.copy(data),
                                          timeout=self.timeout)
                        success = True
                    except (TimeoutError, Full) as e:
                        msg = "Failed putting data in queue: {}".format(e)
                        self.log.warning(msg)
                        if try_ == self.n_tries-1:
                            self.exit_flag.value = False
                            raise e
                        else:
                            self.log.warning("Trying again")
                    if success:
                        break

    def valid_data(self, data):
        """ Validates whether data is valid for the data stream.

        Parameters:
        ===========

        data : list or dict
            Input data which must be validated

        Returns:
        ========

        bool : True if valid data
        """
        if isinstance(data, dict):
            return True
        if isinstance(data, list):
            return True
        return False

    @signal_exit_on_failure
    def on_input_completed(self):
        """ Utility function which wraps the user on_completion function
        and empties data into stream.
        """
        output = self.on_completion()
        if self.valid_data(output):
            self.put_data(data=output)

    @signal_exit_on_failure
    def event_loop(self):
        """ Main event loop. This executes the interior logic of the process.

        Warning:
        =====
        DO NOT OVERWRITE.
        """
        self.log = self._log_()
        self.on_start()

        while self.fail_flag.value and self.exit_flag.value:
            data = self.get_data()
            if data is None:
                continue
            output = self.__process__(data=data)
            if output is None:
                continue
            self.put_data(data=output)
        msg = 'Exiting Loop with flags\tFail:{}\tExit:{}\tInputs:{}'
        self.log.info(msg.format(bool(self.fail_flag.value),
                                 bool(self.exit_flag.value),
                                 bool(self.check_input_flags())))
        self.on_input_completed()
        self.exit_flag.value = False
        if self.outqueue is not None:
            self.outqueue.close()
        if self.inqueue is not None:
            self.inqueue.close()

    def set_input(self, other):
        """ Add an input :class:`StreamElement` to this one. Creates a :class:`Queue`
        between StreamElements in the event there is not an existing one.

        Parameters:
        ===========

        other: :class:`StreamElement`
            An other Stream Element which will stream
            queued data into this one.
        """
        if type(other) is list:
            if self.inqueue is None:
                self.inqueue = Queue(self.queuelen)
            for other_element in other:
                other_element.outqueue = self.inqueue
                self.input_flags.append(other_element.exit_flag)
        elif other.outqueue is None:
            if self.inqueue is None:
                self.inqueue = Queue(self.queuelen)
            other.outqueue = self.inqueue
            self.input_flags.append(other.exit_flag)

    def set_output(self, other):
        """ Sets `self` as an input :class:`StreamElement` to `other`.
        Creates a :class:`Queue` between StreamElements in the event there
        is not an existing one.

        Parameters:
        ===========

        other: :class:`StreamElement`
            An other Stream Element which will stream
            queued data from this one.
        """
        if type(other) is list:
            if self.outqueue is None:
                self.outqueue = Queue(self.queuelen)
            for other_element in other:
                other_element.inqueue = self.outqueue
                other_element.input_flags.append(self.exit_flag)
        elif other.inqueue is None:
            if self.outqueue is None:
                self.outqueue = Queue(self.queuelen)
            other.inqueue = self.outqueue
            other.input_flags.append(self.exit_flag)

    def check_input_flags(self):
        """ Checks to see if the inputs have exited or not.
        Useful as the exiting condition is the Queue is empty and
        the inputs have all finished.

        Returns:
        ========

        bool: True if at least one input is OK.
        """
        if len(self.input_flags) == 0:
            return True
        ret = False
        for flag in self.input_flags:
            ret |= flag.value
        return ret

    @signal_exit_on_failure
    def __process__(self, data):
        """ Wrapper function for :meth:`StreamElement.process`.


        Warning:
        ========

        DO NOT OVERRIDE
        """
        return self.process(data=data)

    @abstractmethod
    def process(self, data):
        """ Abstract method. Implement this for the
        primary action this process will take on `data`

        Parameters:
        ===========

        data: list or dict or None

            Input data to be acted on. Primary data generators can accept
            None as an input, and produce data.


        Returns:
        ========

        dict or list:
            Data to be processed downstream.
        """
        raise NotImplementedError()

    def on_start(self):
        """ Override this method to perform an
        action at the process' beginning of execution.
        """
        self.log.debug("starting")

    def on_completion(self):
        """ Override this method to perform an
        action at the process' end of execution.
        """
        self.log.debug("completing")


def exit_flag():
    """ Convenience function for
    creating the exit flag data type instance.
    """
    return Value('b', True)
