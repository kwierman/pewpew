# -*- coding: utf-8 -*-

"""
test_pewpew
----------------------------------
Tests for `pewpew` module.
"""

import unittest
import pytest
import sys
from contextlib import contextmanager

from pewpew.base import StreamElement, exit_flag


class MyStreamElement(StreamElement):

    def process(self, data):
        print("In Process!")
        self.exit_flag = False
        return None


class TestStreamElement(unittest.TestCase):

    def setUp(self):
        self.exit_flag = exit_flag()

    def tearDown(self):
        self.exit_flag = None

    def test_init(self):
        instance = MyStreamElement(self.exit_flag)
        assert(instance.timeout == 120)
        assert(instance.exit_flag.value)

    def test_signal_on_failure(self):
        self.exit_flag.value = True
        instance = MyStreamElement(self.exit_flag)
        instance.process = lambda x: x.not_a_method
        with pytest.raises(Exception) as excinfo:
            instance.run()
        assert(not instance.fail_flag.value)
        self.exit_flag.value = True

    def test_run(self):
        self.exit_flag.value = False
        instance = MyStreamElement(self.exit_flag)
        instance.start()
        self.exit_flag.value = True
        instance.join()
        assert(not instance.is_alive())

    def test_get_data(self):
        self.exit_flag.value = False
        instance = MyStreamElement(self.exit_flag)
        instance.get_data()

    def test_put_data(self):
        self.exit_flag.value = False
        instance = MyStreamElement(self.exit_flag)
        instance.put_data(data={})

    def test_valid_data(self):
        self.exit_flag.value = False
        instance = MyStreamElement(self.exit_flag)
        assert(instance.valid_data({}))
        assert(instance.valid_data([]))
        assert(not instance.valid_data(None))

    def test_on_completed(self):
        self.exit_flag.value = False
        instance = MyStreamElement(self.exit_flag)
        instance.run()
        assert(instance.exit_flag.value == False)

    def test_set_input(self):
        inst1 = MyStreamElement(self.exit_flag)
        inst2 = MyStreamElement(self.exit_flag)
        q_tst = 8 # setting a queue to a number
        inst1.outqueue = q_tst
        inst1.set_output(inst2)
        assert(inst2.inqueue == q_tst)
        inst2.set_output(inst1)
        from multiprocessing import Queue
        assert(type(inst1.inqueue) == type(inst2.outqueue))

    def test_set_output(self):
        inst1 = MyStreamElement(self.exit_flag)
        inst2 = MyStreamElement(self.exit_flag)
        q_tst = 8 # setting a queue to a number
        inst1.inqueue = q_tst
        inst1.set_input(inst2)
        assert(inst2.outqueue == q_tst)
