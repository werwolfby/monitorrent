import os
from path import path
import falcon
import mimetypes
import json
import datetime
from cherrypy import wsgiserver
from monitorrent.engine import Logger, EngineRunner
from monitorrent.db import init_db_engine, create_db, upgrade
from monitorrent.plugin_managers import load_plugins, get_all_plugins, upgrades, TrackersManager, ClientsManager
from monitorrent.plugins.trackers import TrackerPluginWithCredentialsBase
from monitorrent.settings_manager import SettingsManager
from functools import wraps

def add_static_route(self, folder):
    p = path(folder)
    app.add_route('/', StaticFiles(folder))
    for f in p.walkdirs():
        parts = filter(None, f.splitall())
        url = '/' + '/'.join(parts[1:]) + '/{filename}'
        app.add_route(url, StaticFiles(f))

setattr(falcon.API, 'add_static_route', add_static_route)

init_db_engine("sqlite:///monitorrent.db", True)
load_plugins()
upgrade(get_all_plugins(), upgrades)
create_db()

tracker_manager = TrackersManager()
clients_manager = ClientsManager()

settings_manager = SettingsManager()


class MonitorrentJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime.datetime):
            return o.isoformat()
        return super(MonitorrentJSONEncoder, self).default(o)


class MonitorrentRequest(falcon.Request):
    json = None


class MonitorrentResponse(falcon.Response):
    json = None


# noinspection PyMethodMayBeStatic,PyMethodMayBeStatic,PyUnusedLocal
class JSONTranslator(object):
    def prepare_resource(self, req, resp):
        # req.stream corresponds to the WSGI wsgi.input environ variable,
        # and allows you to read bytes from the request body.
        #
        # See also: PEP 3333
        if req.content_length in (None, 0):
            # Nothing to do
            return

        body = req.stream.read()
        if not body:
            raise falcon.HTTPBadRequest('Empty request body',
                                        'A valid JSON document is required.')

        try:
            req.json = json.loads(body.decode('utf-8'))

        except (ValueError, UnicodeDecodeError):
            raise falcon.HTTPError(falcon.HTTP_753,
                                   'Malformed JSON',
                                   'Could not decode the request body. The '
                                   'JSON was incorrect or not encoded as '
                                   'UTF-8.')

    def process_response(self, req, resp, resource):
        if not resp.json:
            return

        resp.body = json.dumps(resp.json, cls=MonitorrentJSONEncoder, encoding='utf-8', ensure_ascii=False)


# noinspection PyUnusedLocal
class StaticFiles(object):
    def __init__(self, folder=None):
        self.folder = folder

    def on_get(self, req, resp, filename=None):
        file_path = filename or 'index.html'
        if self.folder:
            file_path = os.path.join(self.folder, file_path)
        mime_type, encoding = mimetypes.guess_type(file_path)
        resp.content_type = mime_type
        resp.stream = open(file_path, mode='rb')


# noinspection PyUnusedLocal
class AuthenticationSettings(object):
    def __init__(self, settings_manager):
        self.settings_manager = settings_manager

    def on_get(self, req, resp):
        resp.json = {'is_authentication_enabled': self.settings_manager.get_is_authentication_enabled()}


# noinspection PyUnusedLocal
class Topics(object):
    def __init__(self, tracker_manager):
        self.tracker_manager = tracker_manager

    def on_get(self, req, resp):
        resp.json = self.tracker_manager.get_watching_torrents()

    def on_post(self, req, resp):
        body = req.json
        url = body.get('url', None)
        settings = body.get('settings', None)
        added = self.tracker_manager.add_topic(url, settings)
        if not added:
            raise falcon.HTTPBadRequest('CantAdd', 'Can\'t add torrent: \'{}\''.format(url))
        resp.status = 201


class TopicParse(object):
    def __init__(self, tracker_manager):
        self.tracker_manager = tracker_manager

    def on_get(self, req, resp):
        url = req.get_param('url', required=True)
        title = self.tracker_manager.prepare_add_topic(url)
        if not title:
            raise falcon.HTTPBadRequest('CantParse', 'Can\' parse url: \'{}\''.format(url))
        resp.json = title


app = falcon.API(request_type=MonitorrentRequest, response_type=MonitorrentResponse,
                 middleware=[JSONTranslator()])

app.add_static_route('webapp')
app.add_route('/api/settings/authentication', AuthenticationSettings(settings_manager))
app.add_route('/api/topics', Topics(tracker_manager))
app.add_route('/api/parse', TopicParse(tracker_manager))

if __name__ == '__main__':
    d = wsgiserver.WSGIPathInfoDispatcher({'/': app})
    server = wsgiserver.CherryPyWSGIServer(('0.0.0.0', 8080), d)

    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()
