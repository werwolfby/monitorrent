#!/usr/bin/env python
from builtins import range
import os
import sys
import six
import random
import string
import argparse
import warnings
from cherrypy import wsgiserver
from monitorrent.engine import DBEngineRunner, DbLoggerWrapper, ExecuteLogManager
from monitorrent.db import init_db_engine, create_db
from monitorrent.plugin_managers import load_plugins, get_plugins, TrackersManager, DbClientsManager, NotifierManager
from monitorrent.rest.notifiers import NotifierCollection, Notifier, NotifierCheck, NotifierEnabled
from monitorrent.upgrade_manager import upgrade
from monitorrent.settings_manager import SettingsManager
from monitorrent.rest import create_api, AuthMiddleware
from monitorrent.rest.static_file import StaticFiles
from monitorrent.rest.login import Login, Logout
from monitorrent.rest.topics import TopicCollection, TopicParse, Topic, TopicResetStatus
from monitorrent.rest.trackers import TrackerCollection, Tracker, TrackerCheck
from monitorrent.rest.clients import ClientCollection, Client, ClientCheck, ClientDefault
from monitorrent.rest.settings_authentication import SettingsAuthentication
from monitorrent.rest.settings_password import SettingsPassword
from monitorrent.rest.settings_execute import SettingsExecute
from monitorrent.rest.settings_developer import SettingsDeveloper
from monitorrent.rest.settings_logs import SettingsLogs
from monitorrent.rest.execute import ExecuteLogCurrent, ExecuteCall
from monitorrent.rest.execute_logs import ExecuteLogs
from monitorrent.rest.execute_logs_details import ExecuteLogsDetails


def add_static_route(api, files_dir):
    file_dir = os.path.dirname(os.path.realpath(__file__))
    static_dir = os.path.join(file_dir, files_dir)
    api.add_route('/', StaticFiles(static_dir, 'index.html'))
    api.add_route('/favicon.ico', StaticFiles(static_dir, 'favicon.ico', False))
    api.add_route('/styles/monitorrent.css', StaticFiles(os.path.join(static_dir, 'styles'), 'monitorrent.css', False))
    api.add_route('/login', StaticFiles(static_dir, 'login.html', False))
    for d, dirnames, files in os.walk(static_dir):
        parts = d[len(file_dir)+1:].split(os.path.sep)
        url = '/' + '/'.join(parts[1:] + ['{filename}'])
        api.add_route(url, StaticFiles(d))


def create_app(secret_key, token, tracker_manager, clients_manager, notifier_manager, settings_manager,
               engine_runner, log_manager):
    AuthMiddleware.init(secret_key, token, lambda: settings_manager.get_is_authentication_enabled())
    app = create_api()
    add_static_route(app, 'webapp')
    app.add_route('/api/login', Login(settings_manager))
    app.add_route('/api/logout', Logout())
    app.add_route('/api/topics', TopicCollection(tracker_manager))
    app.add_route('/api/topics/{id}', Topic(tracker_manager))
    app.add_route('/api/topics/{id}/reset_status', TopicResetStatus(tracker_manager))
    app.add_route('/api/topics/parse', TopicParse(tracker_manager))
    app.add_route('/api/trackers', TrackerCollection(tracker_manager))
    app.add_route('/api/trackers/{tracker}', Tracker(tracker_manager))
    app.add_route('/api/trackers/{tracker}/check', TrackerCheck(tracker_manager))
    app.add_route('/api/clients', ClientCollection(clients_manager))
    app.add_route('/api/clients/{client}', Client(clients_manager))
    app.add_route('/api/clients/{client}/check', ClientCheck(clients_manager))
    app.add_route('/api/clients/{client}/default', ClientDefault(clients_manager))
    app.add_route('/api/notifiers', NotifierCollection(notifier_manager))
    app.add_route('/api/notifiers/{notifier}', Notifier(notifier_manager))
    app.add_route('/api/notifiers/{notifier}/check', NotifierCheck(notifier_manager))
    app.add_route('/api/notifiers/{notifier}/enabled', NotifierEnabled(notifier_manager))
    app.add_route('/api/settings/authentication', SettingsAuthentication(settings_manager))
    app.add_route('/api/settings/password', SettingsPassword(settings_manager))
    app.add_route('/api/settings/developer', SettingsDeveloper(settings_manager))
    app.add_route('/api/settings/logs', SettingsLogs(settings_manager))
    app.add_route('/api/settings/execute', SettingsExecute(engine_runner))
    app.add_route('/api/execute/logs', ExecuteLogs(log_manager))
    app.add_route('/api/execute/logs/{execute_id}/details', ExecuteLogsDetails(log_manager))
    app.add_route('/api/execute/logs/current', ExecuteLogCurrent(log_manager))
    app.add_route('/api/execute/call', ExecuteCall(engine_runner))
    return app


def main():
    def try_int(s, base=10, val=None):
        if s is None:
            return None
        try:
            return int(s, base)
        except ValueError:
            return val

    class Config(object):
        debug = False
        ip = '0.0.0.0'
        port = 6687
        db_path = 'monitorrent.db'
        config = 'config.py'

        def __init__(self, parsed_args):
            if parsed_args.config is not None and not os.path.isfile(parsed_args.config):
                warnings.warn('File not found: {}'.format(parsed_args.config))
            config_path = parsed_args.config or self.config
            if os.path.isfile(config_path):
                # noinspection PyBroadException
                try:
                    parsed_config = {}
                    with open(config_path) as config_file:
                        six.exec_(compile(config_file.read(), config_path, 'exec'), {}, parsed_config)
                    self.debug = parsed_config.get('debug', self.debug)
                    self.ip = parsed_config.get('ip', self.ip)
                    self.port = parsed_config.get('port', self.port)
                    self.db_path = parsed_config.get('db_path', self.db_path)
                except:
                    ex, val, tb = sys.exc_info()
                    warnings.warn('Error reading: {0}: {1} ({2}'.format(parsed_args.config, ex, val))

            env_debug = (os.environ.get('MONITORRENT_DEBUG', None) in ['true', 'True', '1'])

            self.debug = parsed_args.debug or env_debug or self.debug
            self.ip = parsed_args.ip or os.environ.get('MONITORRENT_IP', None) or self.ip
            self.port = parsed_args.port or try_int(os.environ.get('MONITORRENT_PORT', None)) or self.port
            self.db_path = parsed_args.db_path or os.environ.get('MONITORRENT_DB_PATH', None) or self.db_path

    parser = argparse.ArgumentParser(description='Monitorrent server')
    parser.add_argument('--debug', action='store_true',
                        help='Run in debug mode. Secret key is always the same.')
    parser.add_argument('--ip', type=str, dest='ip',
                        help='Bind interface. Default is {0}'.format(Config.ip))
    parser.add_argument('--port', type=int, dest='port',
                        help='Port for server. Default is {0}'.format(Config.port))
    parser.add_argument('--db-path', type=str, dest='db_path',
                        help='Path to SQL lite database. Default is to {0}'.format(Config.db_path))
    parser.add_argument('--config', type=str, dest='config',
                        default=os.environ.get('MONITORRENT_CONFIG', None),
                        help='Path to config file (default {0})'.format(Config.config))

    parsed_args = parser.parse_args()
    config = Config(parsed_args)

    db_connection_string = "sqlite:///" + config.db_path

    init_db_engine(db_connection_string, False)
    load_plugins()
    upgrade()
    create_db()

    settings_manager = SettingsManager()
    tracker_manager = TrackersManager(settings_manager.tracker_settings, get_plugins('tracker'))
    clients_manager = DbClientsManager(get_plugins('client'), settings_manager)
    notifier_manager = NotifierManager(get_plugins('notifier'))

    log_manager = ExecuteLogManager()
    engine_runner_logger = DbLoggerWrapper(None, log_manager, settings_manager)
    engine_runner = DBEngineRunner(engine_runner_logger, tracker_manager, clients_manager)

    debug = config.debug

    if debug:
        secret_key = 'Secret!'
        token = 'monitorrent'
    else:
        secret_key = os.urandom(24)
        token = ''.join(random.choice(string.ascii_letters) for _ in range(8))

    app = create_app(secret_key, token, tracker_manager, clients_manager, notifier_manager, settings_manager,
                     engine_runner, log_manager)
    d = wsgiserver.WSGIPathInfoDispatcher({'/': app})
    server_start_params = (config.ip, config.port)
    server = wsgiserver.CherryPyWSGIServer(server_start_params, d)
    print('Server started on {0}:{1}'.format(*server_start_params))

    try:
        server.start()
    except KeyboardInterrupt:
        engine_runner.stop()
        server.stop()


if __name__ == '__main__':
    main()
