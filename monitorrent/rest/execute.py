import falcon
import threading
import time
from Queue import Queue
from monitorrent.engine import Logger, EngineRunner, ExecuteLogManager


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
    def __init__(self, log_manager):
        """
        :type log_manager: ExecuteLogManager
        """
        self.log_manager = log_manager

    def on_get(self, req, resp, after=None):
        if after is not None and not after.isdigit():
            raise falcon.HTTPBadRequest("wrong execute_id", "execute_id schould be specified and schould be int")

        start = time.time()
        result = []
        while True:
            result = self.log_manager.get_current_execute_log_details(after) or []
            if len(result) == 0 and time.time() - start < 30:
                time.sleep(0.1)
            else:
                break

        resp.json = {'is_running': self.log_manager.is_running(), 'logs': result}


# noinspection PyUnusedLocal
class ExecuteCall(object):
    def __init__(self, engine_runner):
        """
        :type engine_runner: EngineRunner
        """
        self.engine_runner = engine_runner

    def on_post(self, req, resp):
        self.engine_runner.execute()
