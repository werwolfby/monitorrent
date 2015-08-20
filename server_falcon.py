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

init_db_engine("sqlite:///monitorrent.db", True)
load_plugins()
upgrade(get_all_plugins(), upgrades)
create_db()

tracker_manager = TrackersManager()
clients_manager = ClientsManager()

settings_manager = SettingsManager()


def default(o):
    if isinstance(o, datetime.datetime):
        return o.isoformat()
    return o


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
        resp.body = json.dumps({'is_authentication_enabled': self.settings_manager.get_is_authentication_enabled()})


# noinspection PyUnusedLocal
class Topics(object):
    def __init__(self, tracker_manager):
        self.tracker_manager = tracker_manager

    def on_get(self, req, resp):
        resp.json = self.tracker_manager.get_watching_torrents()
        resp.body = json.dumps(self.tracker_manager.get_watching_torrents(), default=default)

    def on_post(self, req, resp):
        json = req.get_json()
        url = json.get('url', None)
        settings = json.get('settings', None)
        added = tracker_manager.add_topic(url, settings)
        if not added:
            raise falcon.HTTPBadRequest(message='Can\'t add torrent: \'{}\''.format(url))
        resp.status = 201


app = falcon.API()

p = path('webapp')
app.add_route('/', StaticFiles('webapp'))
for f in p.walkdirs():
    parts = filter(None, f.splitall())
    url = '/' + '/'.join(parts[1:]) + '/{filename}'
    app.add_route(url, StaticFiles(f))
app.add_route('/api/settings/authentication', AuthenticationSettings(settings_manager))
app.add_route('/api/topics', Topics(tracker_manager))

if __name__ == '__main__':
    d = wsgiserver.WSGIPathInfoDispatcher({'/': app})
    server = wsgiserver.CherryPyWSGIServer(('0.0.0.0', 8080), d)

    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()
