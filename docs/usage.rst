Usage
=====


The idea of this package is to subclass the base :class:`pewpew.base.StreamElement` class and then instantiate analysis classes as processes and 
start each in turn.

An example is given here of a concrete implementation.

.. code-block:: python

    class MyProcess(StreamElement):
        def __init__(self, exit_flag, inqueue=None, outqueue=None, **kwargs):
            """ You must absolutely call the StreamElement constructor
            """
            super(MyProcess, self).__init__(exit_flag, inqueue=None,
                                         outqueue=None, **kwargs)
            self.myvar = kwargs.get("my_variable", "default_value")

        def process(self, data):
            """ Override this class (it's necessary) to process data
            """
            data['data']['my field'] = data['data']['my_input_field']*1e9



One may then link modules together and start the processes


.. code-block:: python

    global_exit_flag = exit_flag()

    reader = Reader(global_exit_flag)
    proc = MyProcess(global_exit_flag)
    writer = Writer(global_exit_flag)
    reader.set_output(proc)
    writer.set_input(proc)

    reader.start()
    writer.start()
    proc.start()


    reader.join()
    proc.join()
    writer.join()
