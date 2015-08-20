from cherrypy import wsgiserver
from monitorrent.engine import Logger, EngineRunner
from monitorrent.db import init_db_engine, create_db, upgrade
from monitorrent.plugin_managers import load_plugins, get_all_plugins, upgrades, TrackersManager, ClientsManager
from monitorrent.plugins.trackers import TrackerPluginWithCredentialsBase
from monitorrent.settings_manager import SettingsManager
from monitorrent.rest import create_api
from monitorrent.rest.settings_authentication import SettingsAuthentication
from monitorrent.rest.topics import TopicCollection, TopicParse, Topic

init_db_engine("sqlite:///monitorrent.db", True)
load_plugins()
upgrade(get_all_plugins(), upgrades)
create_db()

tracker_manager = TrackersManager()
clients_manager = ClientsManager()
settings_manager = SettingsManager()

app = create_api('webapp')
app.add_route('/api/settings/authentication', SettingsAuthentication(settings_manager))
app.add_route('/api/topics', TopicCollection(tracker_manager))
app.add_route('/api/topics/{id}', Topic(tracker_manager))
app.add_route('/api/parse', TopicParse(tracker_manager))

if __name__ == '__main__':
    d = wsgiserver.WSGIPathInfoDispatcher({'/': app})
    server = wsgiserver.CherryPyWSGIServer(('0.0.0.0', 8080), d)

    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()
