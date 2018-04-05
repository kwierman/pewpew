from ..base import StreamElement
import logging
import csv
import os


class Writer(StreamElement):
    log = logging.getLogger('pewpew.csv.writer')

    def on_start(self):
        self.output_name = self.config.get("filename", "output")
        self.n_events = self.config.get("events_per_file", None)
        self.output_path = self.config.get("output_path", ".")
        self.output_file = None
        self.writer = None
        self.columns = None
        self.current_cycle = 0
        self.current_event = 0

    @property
    def filename(self):
        return "{}_{}.csv".format(self.output_name, self.current_cycle)

    @property
    def path(self):
        return os.path.join(self.output_path, self.filename)

    def on_completion(self):
        self.log.info("Closing out file and stream")
        self.output_file.close()
        self.output_file = None
        self.writer = None

    def process(self, data):
        if self.n_events is not None:
            if self.current_event == self.n_events:
                msg = "closing out file: {} with events {}/{}"
                msg = msg.format(self.path, self.current_event,
                                 self.n_events)
                self.log.debug(msg)
                self.output_file.close()
                self.output_file = None
                self.current_event = 0
                self.current_cycle += 1

        if self.output_file is None:
            if os.path.exists(self.path):
                msg = "output path already exists. replacing {}"
                self.log.warning(msg.format(self.path))
                os.remove(self.path)
            self.output_file = open(self.path, 'w')
            self.current_cycle += 1
            field_names = [i for i in data['data'].keys()]
            self.writer = csv.DictWriter(self.output_file,
                                         fieldnames=field_names)
        self.writer.writerow(data['data'])
