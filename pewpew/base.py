from multiprocessing import Process, Queue, TimeoutError, Value
from multiprocessing.queues import Empty
from abc import abstractmethod, ABCMeta
import logging
import copy


class StreamElement(Process):

    log = logging.getLogger('pewpew.streamelement')
    __metaclass__ = ABCMeta

    def __init__(self, exit_flag, inqueue=None, outqueue=None, **kwargs):
        super(StreamElement, self).__init__()
        self.inqueue = inqueue
        self.outqueue = outqueue
        self.kwargs = kwargs
        self.exit_flag = exit_flag
        self.graceful_exit = True
        self.timeout = int(kwargs.get("timeout", 120))
        self.queuelen = int(kwargs.get("default_queuelen", 10))

    def signal_exit_on_failure(fn):
        def wrapped(self=None, **kwargs):
            try:
                return fn(self, **kwargs)
            except Exception:
                self.log.info("signaling exit to all processes")
                self.exit_flag.value = False
                raise
        return wrapped

    def run(self):
        self.event_loop()
        msg = "exiting with flags {} {}"
        self.log.info(msg.format(self.exit_flag.value,
                                 self.graceful_exit))

    @signal_exit_on_failure
    def get_data(self):
        if self.inqueue is not None:
            try:
                return self.inqueue.get(timeout=self.timeout)
            except (TimeoutError, Empty):
                self.graceful_exit = False
                return None
        return {}

    @signal_exit_on_failure
    def put_data(self, data):
        if not self.valid_data(data):
            msg = "cannot understand output data type: {}"
            self.log.warning(msg.format(type(data)))
            return
        if self.outqueue is not None:
            if isinstance(data, list):
                for i in data:
                    self.outqueue.put(copy.copy(i), timeout=self.timeout)
            else:
                self.outqueue.put(copy.copy(data), timeout=self.timeout)

    def valid_data(self, data):
        if isinstance(data, dict):
            return True
        if isinstance(data, list):
            return True
        return False

    @signal_exit_on_failure
    def on_input_completed(self):
        self.log.info("received completed from upstream")
        output = self.on_completion()
        if self.valid_data(output):
            self.put_data(data=output)

    @signal_exit_on_failure
    def event_loop(self):
        self.on_start()
        while self.exit_flag.value and self.graceful_exit:
            data = self.get_data()
            if data is None:
                continue
            output = self.__process__(data=data)
            if output is None:
                continue
            self.put_data(data=output)
        self.on_input_completed()

    def set_input(self, other):
        if type(other) is list:
            if self.inqueue is None:
                self.inqueue = Queue(self.queuelen)
            for other_element in other:
                other_element.outqueue = self.inqueue
        elif other.outqueue is None:
            if self.inqueue is None:
                self.inqueue = Queue(self.queuelen)
            other.outqueue = self.inqueue

    def set_output(self, other):
        if type(other) is list:
            if self.outqueue is None:
                self.outqueue = Queue(self.queuelen)
            for other_element in other:
                other_element.inqueue = self.outqueue
        elif other.inqueue is None:
            if self.outqueue is None:
                self.outqueue = Queue(self.queuelen)
            other.inqueue = self.outqueue

    @signal_exit_on_failure
    def __process__(self, data):
        return self.process(data)

    @abstractmethod
    def process(self, data):
        raise NotImplementedError()

    def on_start(self):
        self.log.debug("starting")

    def on_completion(self):
        self.log.debug("completing")
        self.graceful_exit = False


def exit_flag():
    return Value('b', True)
