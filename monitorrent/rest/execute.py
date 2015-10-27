import json
import threading
from Queue import Queue, Empty
from monitorrent.engine import Logger, EngineRunner


class EngineRunnerLoggerWrapper(Logger):
    """
    :type queues: list[Queue]
    """
    queues = []
    events = []
    queues_lock = threading.Lock()

    def __init__(self, logger):
        """
        :type logger: Logger | None
        """
        self.logger = logger

    def started(self):
        with self.queues_lock:
            self.events = []
        if self.logger:
            self.logger.started()
        self._emit('started', None)

    def finished(self, finish_time, exception):
        if self.logger:
            self.logger.finished(finish_time, exception)
        args = {
            'finish_time': finish_time.isoformat(),
            'exception': exception.message if exception else None
        }
        self._emit('finished', args)
        with self.queues_lock:
            for q in self.queues:
                # close queue
                q.put(None, False)
            self.events = []

    def info(self, message):
        if self.logger:
            self.logger.info(message)
        self._emit_log('info', message)

    def failed(self, message):
        if self.logger:
            self.logger.failed(message)
        self._emit_log('failed', message)

    def downloaded(self, message, torrent):
        if self.logger:
            self.logger.downloaded(message, torrent)
        self._emit_log('downloaded', message, size=len(torrent))

    def attach(self, queue):
        """
        :type queue: Queue
        """
        with self.queues_lock:
            self.queues.append(queue)
            for e in self.events:
                queue.put(e, False)

    def detach(self, queue):
        """
        :type queue: Queue
        """
        with self.queues_lock:
            if queue in self.queues:
                self.queues.remove(queue)

    def _emit(self, event, data):
        data = {'event': event, 'data': data}
        with self.queues_lock:
            for q in self.queues:
                q.put(data, False)
            self.events.append(data)

    def _emit_log(self, level, message, **kwargs):
        data = {'level': level, 'message': message}
        data.update(kwargs)
        self._emit('log', data)


# noinspection PyUnusedLocal
class ExecuteLogCurrent(object):
    def __init__(self, logger, timeout=30):
        """
        :type logger: EngineRunnerLoggerWrapper
        :type timeout: int
        """
        self.logger = logger
        self.timeout = timeout

    def _response(self, queue):
        self.logger.attach(queue)
        try:
            yield "["
            first = True
            while True:
                try:
                    data = queue.get(timeout=self.timeout)
                except Empty:
                    break
                if data is None:
                    break
                comma = ','
                if first:
                    first = False
                    comma = ''
                yield comma + json.dumps(data)
            yield "]"
        except GeneratorExit:
            pass
        finally:
            self.logger.detach(queue)

    def on_get(self, req, resp):
        queue = Queue()
        resp.stream = self._response(queue)


# noinspection PyUnusedLocal
class ExecuteCall(object):
    def __init__(self, engine_runner):
        """
        :type engine_runner: EngineRunner
        """
        self.engine_runner = engine_runner

    def on_post(self, req, resp):
        self.engine_runner.execute()
