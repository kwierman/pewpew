from ..base import StreamElement
from celery import current_app
from celery.bin import worker


class Worker(StreamElement):

    def on_start(self):
        self.app = current_app._get_current_object()
        self.worker = worker.worker(app=self.app)

        broker = self.config.get('broker',
                                 'amqp://guest:guest@localhost:5672//')
        loglevel = self.config.get('loglevel', 'INFO')
        traceback = self.config.get('traceback', True)

        options = {'broker': broker,
                   'loglevel': loglevel,
                   'traceback': traceback}
        self.worker.run(**options)

    def on_completion(self):
        pass

    def process(self, data):
        pass
