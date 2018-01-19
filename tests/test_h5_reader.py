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

from pewpew.hdf5 import Reader
from pewpew.base import exit_flag
from multiprocessing import Value
from mock import patch, MagicMock


class TestH5Reader(unittest.TestCase):

    def setUp(self):
        self.exit_flag = exit_flag()
        self.patcher = patch('h5py.File')
        self.patcher.start()

    def tearDown(self):
        self.exit_flag = None
        self.patcher.stop()

    def test_init_(self):
        reader = Reader(self.exit_flag, file_list=['myfile.h5'])
        assert(len(reader.file_list)==1)
