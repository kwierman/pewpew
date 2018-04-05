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

from pewpew.hdf5 import Writer
from pewpew.base import exit_flag
from multiprocessing import Value
from mock import patch


class TestH5Writer(unittest.TestCase):

    def setUp(self):
        self.exit_flag = exit_flag()
        self.patcher = patch('h5py.File')
        self.patcher.start()

    def tearDown(self):
        self.exit_flag = None
        self.patcher.stop()

    def test_init_(self):
        reader = Writer(self.exit_flag)
