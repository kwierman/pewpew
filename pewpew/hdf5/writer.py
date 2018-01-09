from ..base import StreamElement, NullOp
import logging
import h5py
import os


class Writer(StreamElement):
  log = logging.getLogger('pewpew.writer')

  def __init__(self, exit_flag, inqueue=None, outqueue=None, **kwargs):
    super(Writer, self).__init__(exit_flag, inqueue=None,
                                outqueue=None, **kwargs)

    self.output_name = kwargs.get("filename", "output")
    self.n_events = kwargs.get("events_per_file", None)
    self.output_path = kwargs.get("output_path", ".")
    self.chunk_size = kwargs.get('chunk_size', 1)
    self.output_file = None
    self.current_cycle = 0
    self.current_event = 0
    self.output_datasets = {}

  @property
  def filename(self):
    return "{}_{}.h5".format(self.output_name, self.current_cycle)

  @property
  def path(self):
    return os.path.join(self.output_path, self.filename)

  def process_metadata(self, meta):
    for obj in meta:
      for key in meta[obj]:
         self.output_file[obj].attrs[key] = meta[obj][key]
    self.log.info("wrote metadata")

  def process_data(self, data):
    for dataname in data.keys():
      new_shape = (self.current_event + 1, )
      new_shape = new_shape + self.output_datasets[dataname].shape[1:]
      self.output_datasets[dataname].resize(new_shape)
      self.output_datasets[dataname][self.current_event] = data[dataname]
    self.current_event += 1
    self.log.debug("Now on event {}/{}".format(self.current_event,
                                               self.n_events))

  def on_completion(self):
    self.log.info("Closing out file and stream")
    self.output_file.close()
    self.output_file = None
    self.exit_flag.value = False

  def process(self, data):
    if self.n_events is not None:
      if self.current_event == self.n_events:
        msg = "closing out file: {} with events {}/{}"
        msg = msg.format(self.path, self.current_event,
                         self.n_events)
        self.log.debug(msg)
        self.output_datasets = {}
        self.output_file.close()
        self.output_file = None
        self.current_event = 0

    process_meta = self.output_file is None
    if process_meta:
      if os.path.exists(self.path):
        msg = "output path already exists. replacing {}"
        self.log.warning(msg.format(self.path))
        os.remove(self.path)
      self.output_file = h5py.File(self.path, 'w')
      self.current_cycle +=1
      for dataname in data['data'].keys():
        b_shape = (self.chunk_size, ) + data['data'][dataname].shape
        max_shape = (None, ) + data['data'][dataname].shape
        self.log.debug("creating dataset {} with shape {}".format(dataname,
                                                                  b_shape))
        tmp_dataset = self.output_file.create_dataset(dataname,
                                                      b_shape,
                                                      maxshape=max_shape,
                                                      chunks=b_shape,
                                                      dtype='float',
                                                      compression="lzf")
        self.output_datasets[dataname] = tmp_dataset

    self.process_data(data['data'])
    if process_meta:
      self.process_metadata(data['meta'])
    return NullOp()