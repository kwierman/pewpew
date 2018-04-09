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
from multiprocessing import Queue, Value


class SingleStreamElement(StreamElement):
    def process(self, data):
        assert(data is not None)
        self.exit_flag.value = False
        return data


class MultiStreamElement(StreamElement):

    def on_start(self):
        self.counter = Value('i',0)

    def process(self, data):
        assert(data is not None)
        self.counter.value += 1
        return data

    def on_completion(self):
        assert(self.counter.value == 10)


class TestDataStream(unittest.TestCase):

    def test_data_insertion(self):
        queue = Queue()
        instance = SingleStreamElement()
        instance.inqueue = queue
        queue.put({'data':None, 'meta':None})
        instance.start()
        instance.join()
        assert(not instance.is_alive())
        assert(queue.empty())
        instance = None

    def test_double_data_insertion(self):
        queue = Queue()
        flag = Value('b', True)
        instance = SingleStreamElement()
        instance.inqueue = queue
        instance.input_flags.append(flag)
        for _ in range(10): 
            queue.put({'data':None, 'meta':None})
        instance.start()
        flag.value = False
        instance.join()
        assert(not instance.is_alive())
        assert(not queue.empty())
        instance = None

    def test_exit_flag_functionality(self):
        queue = Queue()
        flag = Value('b', True)
        instance = MultiStreamElement()
        instance.inqueue = queue
        instance.input_flags.append(flag)
        for _ in range(10): 
            queue.put({'data':None, 'meta':None})
        instance.start()
        flag.value = False
        instance.join()
        #assert(queue.empty())
        assert(not instance.is_alive())
        instance = None
