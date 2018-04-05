from ..base import StreamElement
import logging
import csv


class Reader(StreamElement):
    log = logging.getLogger('pewpew.csv.reader')

    converters = []

    def on_start(self):

        self.file_list = self.config.get('file_list', [])
        self.repeat = self.config.get('repeat', False)
        self.dialect = self.config.get('dialect', 'excell')
        self.delimiter = self.config.get('delimiter', ',')
        self.quote_char = self.config.get("quote_char", '|')
        self.file_iter = None
        self.file = None
        self.reader = None
        self.event_iter = None
        self.field_names = None

    def _file_iter_(self):
        for file_ in self.file_list:
            yield open(file_, 'rb')

    def process(self, data=None):
        while self.file is None:
            if self.file_iter is None:
                self.file_iter = self._file_iter_()
            try:
                self.file = next(self.file_iter)
                self.reader = csv.DictReader(self.file,
                                             dialect=self.dialect,
                                             delimiter=self.delimiter,
                                             quote_char=self.quote_char)
                self.event_iter = iter(self.reader)
                self.log.debug("opening {}".format(self.file))
            except StopIteration:
                self.log.info("hit end of file iter")
                if self.repeat:
                    self.file = None
                    self.file_iter = None
                    self.reader = None
                    self.event_iter = None
                else:
                    return None
        try:
            return {'data': next(self.event_iter)}
        except StopIteration:
            self.log.info("hit end of file")
            self.file = None
            self.file_iter = None
            self.reader = None
            self.event_iter = None
