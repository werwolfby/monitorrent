import os, random, string
import mimetypes
import falcon
import threading
import json
from Queue import Queue, Empty
from cherrypy import wsgiserver
from path import path
from monitorrent.engine import Logger, DBEngineRunner
from monitorrent.db import init_db_engine, create_db, upgrade
from monitorrent.plugin_managers import load_plugins, get_all_plugins, upgrades, TrackersManager, ClientsManager
from monitorrent.settings_manager import SettingsManager
from monitorrent.rest import create_api, AuthMiddleware
from monitorrent.rest.static_file import StaticFiles
from monitorrent.rest.login import Login, Logout
from monitorrent.rest.topics import TopicCollection, TopicParse, Topic
from monitorrent.rest.trackers import TrackerCollection, Tracker, TrackerCheck
from monitorrent.rest.clients import ClientCollection, Client, ClientCheck
from monitorrent.rest.settings_authentication import SettingsAuthentication
from monitorrent.rest.settings_password import SettingsPassword
from monitorrent.rest.settings_execute import SettingsExecute


class EngineRunnerLogger(Logger):
    """
    :type queues: list[Queue]
    """
    queues = []
    events = []
    queues_lock = threading.Lock()

    def started(self):
        with self.queues_lock:
            self.events = []
        self._emit('started', None)

    def finished(self, finish_time, exception):
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
        self._emit_log('info', message)

    def failed(self, message):
        self._emit_log('failed', message)

    def downloaded(self, message, torrent):
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


init_db_engine("sqlite:///monitorrent.db", False)
load_plugins()
upgrade(get_all_plugins(), upgrades)
create_db()

tracker_manager = TrackersManager()
clients_manager = ClientsManager()
settings_manager = SettingsManager()

engine_runner = DBEngineRunner(EngineRunnerLogger(), tracker_manager, clients_manager)


def add_static_route(api, folder):
    p = path(folder)
    api.add_route('/', StaticFiles(folder, 'index.html'))
    api.add_route('/favicon.ico', StaticFiles(folder, 'favicon.ico', False))
    api.add_route('/styles/monitorrent.css', StaticFiles(os.path.join(folder, 'styles'), 'monitorrent.css', False))
    api.add_route('/login', StaticFiles(folder, 'login.html', False))
    for f in p.walkdirs():
        parts = filter(None, f.splitall())
        url = '/' + '/'.join(parts[1:]) + '/{filename}'
        api.add_route(url, StaticFiles(f))

debug = True
if debug:
    secret_key = 'Secret!'
    token = 'monitorrent'
else:
    secret_key = os.urandom(24)
    token = ''.join(random.choice(string.letters) for x in range(8))


# noinspection PyUnusedLocal
class ExecuteLog(object):
    def __init__(self, engine_runner, timeout=30):
        """
        :type engine_runner: EngineRunner
        :type timeout: int
        """
        self.engine_runner = engine_runner
        self.timeout = timeout

    def _response(self, queue):
        generator_exit = False
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
        except GeneratorExit:
            generator_exit = True
        finally:
            if not generator_exit:
                yield "]"
            self.engine_runner.logger.detach(queue)

    def on_get(self, req, resp):
        queue = Queue()
        self.engine_runner.logger.attach(queue)
        resp.stream = self._response(queue)


# noinspection PyUnusedLocal
class ExecuteCall(object):
    def __init__(self, engine_runner, timeout=30):
        """
        :type engine_runner: EngineRunner
        :type timeout: int
        """
        self.engine_runner = engine_runner
        self.timeout = timeout

    def on_post(self, req, resp):
        self.engine_runner.execute()


AuthMiddleware.init(secret_key, token)
app = create_api()
add_static_route(app, 'webapp')
app.add_route('/api/login', Login(settings_manager))
app.add_route('/api/logout', Logout())
app.add_route('/api/topics', TopicCollection(tracker_manager))
app.add_route('/api/topics/{id}', Topic(tracker_manager))
app.add_route('/api/topics/parse', TopicParse(tracker_manager))
app.add_route('/api/trackers', TrackerCollection(tracker_manager))
app.add_route('/api/trackers/{tracker}', Tracker(tracker_manager))
app.add_route('/api/trackers/{tracker}/check', TrackerCheck(tracker_manager))
app.add_route('/api/clients', ClientCollection(clients_manager))
app.add_route('/api/clients/{client}', Client(clients_manager))
app.add_route('/api/clients/{client}/check', ClientCheck(clients_manager))
app.add_route('/api/settings/authentication', SettingsAuthentication(settings_manager))
app.add_route('/api/settings/password', SettingsPassword(settings_manager))
app.add_route('/api/settings/execute', SettingsExecute(engine_runner))
app.add_route('/api/execute/logs', ExecuteLog(engine_runner))
app.add_route('/api/execute/call', ExecuteCall(engine_runner))

if __name__ == '__main__':
    d = wsgiserver.WSGIPathInfoDispatcher({'/': app})
    server = wsgiserver.CherryPyWSGIServer(('0.0.0.0', 8080), d)

    try:
        server.start()
    except KeyboardInterrupt:
        engine_runner.stop()
        server.stop()
