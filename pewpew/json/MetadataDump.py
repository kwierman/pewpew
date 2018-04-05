from ..base import StreamElement
import logging
import json
import os


class MetadataDump(StreamElement):
    log = logging.getLogger('pewpew.json.metadata')

    def on_start(self):
        self.output_name = self.config.get("filename", "output")
        self.output_path = self.config.get("output_path", ".")
        self.output_file = None
        self.dump_once = self.config.get("dump_once", True)
        self.n_dumps = 0

    @property
    def path(self):
        return os.path.join(self.output_path, self.output_name)

    def process(self, data):
        if self.n_dumps == 0 or not self.dump_once:
            with open(self.path, 'w') as outfile:
                json.dump(data['meta'], outfile)
        self.n_dumps += 1
        return data
