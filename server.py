import os
import json
import cherrypy
from engine import Logger, EngineRunner
import threading
from db import init_db_engine, create_db
from plugin_managers import load_plugins, TrackersManager, ClientsManager
from ws4py.server.cherrypyserver import WebSocketPlugin, WebSocketTool
from ws4py.websocket import WebSocket

engine = init_db_engine("sqlite:///monitorrent.db", True)
load_plugins()
create_db(engine)

tracker_manager = TrackersManager()
clients_manager = ClientsManager()


class EngineWebSocketLogger(Logger):
    executeWebSockets = []
    _executeWebSocketsLock = threading.Lock()

    def __init__(self):
        pass

    def info(self, message):
        self.send('info', message)

    def failed(self, message):
        self.send('failed', message)

    def downloaded(self, message, torrent):
        self.send('downloaded', message, size=len(torrent))

    def send(self, level, message, **kwargs):
        self.broadcast(json.dumps({'level': level, 'message': message}))

    def broadcast(self, message):
        with self._executeWebSocketsLock:
            wss = list(self.executeWebSockets)
        for ws in wss:
            if not ws.terminated:
                try:
                    ws.send(message)
                except:
                    pass

    @staticmethod
    def append(ws):
        with EngineWebSocketLogger._executeWebSocketsLock:
            EngineWebSocketLogger.executeWebSockets.append(ws)

    @staticmethod
    def remove(ws):
        with EngineWebSocketLogger._executeWebSocketsLock:
            EngineWebSocketLogger.executeWebSockets.remove(ws)

engine_runner = EngineRunner(EngineWebSocketLogger(), tracker_manager, clients_manager)


class ExecuteWebSocket(WebSocket):
    def opened(self):
        EngineWebSocketLogger.append(self)

    def closed(self, code, reason=None):
        EngineWebSocketLogger.remove(self)

    def send(self, payload, binary=False):
        if self.stream is not None:
            return super(ExecuteWebSocket, self).send(payload, binary)

    def received_message(self, message):
        if message.is_text and message.data == "execute":
            engine_runner.execute()


class App(object):
    def __init__(self):
        super(App, self).__init__()
        self.api = Api()

    @cherrypy.expose
    def index(self):
        raise cherrypy.HTTPRedirect("/static/index5.html")

    @cherrypy.expose
    def ws(self):
        cherrypy.log("Handler created: %s" % repr(cherrypy.request.ws_handler))


class Api(object):
    def __init__(self):
        super(Api, self).__init__()
        self.torrents = TorrentsApi()
        self.clients = ClientsApi()
        self.execute = ExecuteApi()

    @cherrypy.expose
    def parse(self, url):
        name = tracker_manager.parse_url(url)
        if name:
            return name
        raise cherrypy.HTTPError(404, "Can't parse url %s" % url)

    @cherrypy.expose
    def check_client(self, client):
        cherrypy.response.status = 200 if clients_manager.check_connection(client) else 500


class TorrentsApi(object):
    exposed = True

    @cherrypy.tools.json_out()
    def GET(self):
        return tracker_manager.get_watching_torrents()

    def DELETE(self, url):
        cherrypy.response.status = 204 if tracker_manager.remove_watch(url) else 404

    @cherrypy.tools.json_in()
    def POST(self):
        result = cherrypy.request.json
        if not result or 'url' not in result:
            raise cherrypy.HTTPError(404, 'missing required url parameter in body')
        cherrypy.response.status = 201 if tracker_manager.add_watch(result['url']) else 400


class ClientsApi(object):
    exposed = True

    @cherrypy.tools.json_out()
    def GET(self, client):
        return clients_manager.get_settings(client)

    @cherrypy.tools.json_in()
    def PUT(self, client):
        settings = cherrypy.request.json
        clients_manager.set_settings(client, settings)
        cherrypy.response.status = 204


class ExecuteApi(object):
    exposed = True

    @cherrypy.tools.json_out()
    def GET(self):
        return {
            "interval": engine_runner.interval,
            "last_execute": engine_runner.last_execute.isoformat() if engine_runner.last_execute else None
        }

    @cherrypy.tools.json_in()
    def PUT(self):
        settings = cherrypy.request.json
        if not settings or 'interval' not in settings:
            raise cherrypy.HTTPError(404, 'missing required url parameter in body')
        engine_runner.interval = int(settings['interval'])
        cherrypy.response.status = 204


if __name__ == '__main__':
    conf = {
        '/': {
            'tools.staticdir.root': os.path.abspath(os.getcwd()),
        },
        '/static': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': './static'
        },
        '/api/torrents': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
        },
        '/api/clients': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
        },
        '/api/execute': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
        },
        '/ws': {
            'tools.websocket.on': True,
            'tools.websocket.handler_cls': ExecuteWebSocket
        },
    }

    WebSocketPlugin(cherrypy.engine).subscribe()
    cherrypy.tools.websocket = WebSocketTool()

    cherrypy.config.update({
        'server.socket_host': '0.0.0.0',
    })
    cherrypy.quickstart(App(), config=conf)
