""" HDF5 File Reader
"""

from ..base import StreamElement
import logging
import h5py
import os


class Reader(StreamElement):
    log = logging.getLogger('pewpew.reader')

    def __init__(self, exit_flag, inqueue=None, outqueue=None, **kwargs):
        super(Reader, self).__init__(exit_flag, inqueue=None,
                                     outqueue=None, **kwargs)
        self.file_list = kwargs.get('file_list', [])
        self.repeat = kwargs.get('repeat', False)
        self.file = None
        self.file_iter = None
        self.event_iter = None
        self._read_list_ = None
        self.metadata = None
        self.data = {}
        self.event_number = None

    def _file_iter_(self):
        """ Returns an iterator over the file list
        """
        for file_ in self.file_list:
            yield h5py.File(file_, 'r')

    def get_dataset(self, input_file):
        """ Walks along the object tree in an HDF5 file and inspects it for
        datasets.


        Parameters:
        ===========

        input_file: h5py.File
            The file to be inspected.
        """

        def walk_tree(obj, path='/'):
            ret = [path]
            t = type(obj)

            if t == h5py._hl.files.File or t == h5py._hl.group.Group:
                for i in obj:
                    child = obj[i]
                    ret = ret + walk_tree(child, os.path.join(path, i))
            return ret

        def filter(item, input_file):
            return type(input_file[item]) == h5py._hl.dataset.Dataset
        ret = [i for i in walk_tree(input_file) if filter(i, input_file)]
        return ret

    def get_metadata(self):
        """ Get a dict of the file attributes and the corresponding objects.
        """
        ret = {}
        for i in self._read_list_:
            ret[i] = {}
            for j in self.file[i].attrs:
                ret[i][j] = self.file[i].attrs[j]
        return ret

    def process(self, data=None):
        """ Takes input `data` and writes to the file.

        This module expects `data` to be a dict with 2 keys:
        'meta' and 'data'. 
        """
        while self.file is None:
            if self.file_iter is None:
                self.file_iter = self._file_iter_()
            try:
                self.file = next(self.file_iter)
                self.log.debug("opening {}".format(self.file))
                self._read_list_ = self.get_dataset(self.file)
                event_range = self.file[self._read_list_[0]].shape[0]
                self.event_iter = iter(range(event_range))
                self.data['meta'] = self.get_metadata()
                self.data['data'] = {}
            except StopIteration:
                self.log.info("hit end of file iter")
                if self.repeat:
                    self.file = None
                    self.file_iter = None
                else:
                    return None
            except Exception as e:
                self.log.warning(e)
                self.file = None
                continue
        try:
            self.event_number = next(self.event_iter)
        except StopIteration:
            msg = "hit end of file at {} event(s)"
            self.log.info(msg.format(self.event_number + 1))
            self.file = None
            return self.process(data)
        for dataset in self._read_list_:
            try:
                tmp = self.file[dataset][self.event_number]
                self.data['data'][dataset] = tmp
            except Exception as e:
                self.log.warning(e)
                self.file = None
                return self.process(data)
        return self.data
