from ..base import StreamElement, NullOp, CompletedOp
import logging
import h5py
import os


def file_iter(file_list):
  for file_ in file_list:
    yield h5py.File(file_, 'r')


def get_dataset(input_file):

  def walk_file_tree(obj, path='/'):
    ret = [path]
    t = type(obj)

    if t == h5py._hl.files.File or t == h5py._hl.group.Group:
      for i in obj:
        child = obj[i]
        ret = ret + walk_file_tree(child, os.path.join(path, i))
    return ret

  def ds_filter(item, input_file):
    return type(input_file[item]) == h5py._hl.dataset.Dataset

  return [i for i in walk_file_tree(input_file) if ds_filter(i, input_file)]


class Reader(StreamElement):
  log = logging.getLogger('lnd.input')

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

  def get_metadata(self):
    ret = {}
    for i in self._read_list_:
      ret[i] = {}
      for j in self.file[i].attrs:
        ret[i][j] = self.file[i].attrs[j]
    return ret

  def process(self, data=None):
    # If no file, then get next
    while self.file is None:
      if self.file_iter is None:
        self.file_iter = file_iter(self.file_list)
      try:
        self.file = next(self.file_iter)
        self.log.debug("opening {}".format(self.file))
        self._read_list_ = get_dataset(self.file)
        self.event_iter = iter(range(self.file[self._read_list_[0]].shape[0]))
        self.data['meta'] = self.get_metadata()
        self.data['data'] = {}
      except StopIteration:
        self.log.info("hit end of file iter")
        if self.repeat:
          self.file = None
          self.file_iter = None
        else:
          return CompletedOp()
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
      return NullOp()
    for dataset in self._read_list_:
      try:
        self.data['data'][dataset] = self.file[dataset][self.event_number]
      except Exception as e:
        self.log.warning(e)
        self.file = None
        return NullOp()
    return self.data
