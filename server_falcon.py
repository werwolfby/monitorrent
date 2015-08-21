import os
import mimetypes
from cherrypy import wsgiserver
from path import path
from monitorrent.engine import Logger, EngineRunner
from monitorrent.db import init_db_engine, create_db, upgrade
from monitorrent.plugin_managers import load_plugins, get_all_plugins, upgrades, TrackersManager, ClientsManager
from monitorrent.plugins.trackers import TrackerPluginWithCredentialsBase
from monitorrent.settings_manager import SettingsManager
from monitorrent.rest import create_api
from monitorrent.rest.settings_authentication import SettingsAuthentication
from monitorrent.rest.topics import TopicCollection, TopicParse, Topic
from monitorrent.rest.trackers import TrackerCollection, Tracker

init_db_engine("sqlite:///monitorrent.db", True)
load_plugins()
upgrade(get_all_plugins(), upgrades)
create_db()

tracker_manager = TrackersManager()
clients_manager = ClientsManager()
settings_manager = SettingsManager()


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


def add_static_route(api, folder):
    p = path(folder)
    api.add_route('/', StaticFiles(folder))
    for f in p.walkdirs():
        parts = filter(None, f.splitall())
        url = '/' + '/'.join(parts[1:]) + '/{filename}'
        api.add_route(url, StaticFiles(f))

app = create_api()
add_static_route(app, 'webapp')
app.add_route('/api/settings/authentication', SettingsAuthentication(settings_manager))
app.add_route('/api/topics', TopicCollection(tracker_manager))
app.add_route('/api/topics/{id}', Topic(tracker_manager))
app.add_route('/api/parse', TopicParse(tracker_manager))
app.add_route('/api/trackers', TrackerCollection(tracker_manager))
app.add_route('/api/trackers/{tracker}', Tracker(tracker_manager))

if __name__ == '__main__':
    d = wsgiserver.WSGIPathInfoDispatcher({'/': app})
    server = wsgiserver.CherryPyWSGIServer(('0.0.0.0', 8080), d)

    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()
