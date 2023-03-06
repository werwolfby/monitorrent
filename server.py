#!/usr/bin/env python
from builtins import range
import os
import sys
import six
import random
import string
import argparse
import warnings
from cheroot import wsgi
from monitorrent.engine import DBEngineRunner, DbLoggerWrapper, ExecuteLogManager
from monitorrent.db import init_db_engine, create_db
from monitorrent.plugin_managers import load_plugins, get_plugins, TrackersManager, DbClientsManager, NotifierManager
from monitorrent.rest.challenge_logs import ChallengeLogs
from monitorrent.rest.notifiers import NotifierCollection, Notifier, NotifierCheck, NotifierEnabled
from monitorrent.upgrade_manager import upgrade
from monitorrent.settings_manager import SettingsManager
from monitorrent.new_version_checker import NewVersionChecker
from monitorrent.rest import create_api, AuthMiddleware
from monitorrent.rest.static_file import StaticFiles
from monitorrent.rest.login import Login, Logout
from monitorrent.rest.topics import TopicCollection, TopicParse, Topic, TopicResetStatus, TopicPauseState
from monitorrent.rest.trackers import TrackerCollection, Tracker, TrackerCheck
from monitorrent.rest.clients import ClientCollection, Client, ClientCheck, DefaultClient, ClientDefault
from monitorrent.rest.settings_authentication import SettingsAuthentication
from monitorrent.rest.settings_password import SettingsPassword
from monitorrent.rest.settings_execute import SettingsExecute
from monitorrent.rest.settings_developer import SettingsDeveloper
from monitorrent.rest.settings_logs import SettingsLogs
from monitorrent.rest.settings_proxy import SettingsProxyEnabled, SettingsProxy
from monitorrent.rest.settings_new_version_checker import SettingsNewVersionChecker
from monitorrent.rest.settings_notify_on import SettingsNotifyOn
from monitorrent.rest.new_version import NewVersion
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
        parts = d[len(file_dir) + 1:].split(os.path.sep)
        url = '/' + '/'.join(parts[1:] + ['{filename}'])
        api.add_route(url, StaticFiles(d))


def create_app(secret_key, token, tracker_manager, clients_manager, notifier_manager, settings_manager,
               engine_runner, log_manager, new_version_checker):
    AuthMiddleware.init(secret_key, token, lambda: settings_manager.get_is_authentication_enabled())
    app = create_api()
    add_static_route(app, 'webapp')
    app.add_route('/api/login', Login(settings_manager))
    app.add_route('/api/logout', Logout())
    app.add_route('/api/topics', TopicCollection(tracker_manager))
    app.add_route('/api/topics/{id}', Topic(tracker_manager))
    app.add_route('/api/topics/{id}/reset_status', TopicResetStatus(tracker_manager))
    app.add_route('/api/topics/{id}/pause', TopicPauseState(tracker_manager))
    app.add_route('/api/topics/parse', TopicParse(tracker_manager))
    app.add_route('/api/trackers', TrackerCollection(tracker_manager))
    app.add_route('/api/trackers/{tracker}', Tracker(tracker_manager))
    app.add_route('/api/trackers/{tracker}/check', TrackerCheck(tracker_manager))
    app.add_route('/api/default_client', DefaultClient(clients_manager))
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
    app.add_route('/api/settings/proxy/enabled', SettingsProxyEnabled(settings_manager))
    app.add_route('/api/settings/proxy', SettingsProxy(settings_manager))
    app.add_route('/api/settings/execute', SettingsExecute(engine_runner))
    app.add_route('/api/settings/new-version-checker', SettingsNewVersionChecker(settings_manager, new_version_checker))
    app.add_route('/api/settings/notify-on', SettingsNotifyOn(settings_manager))
    app.add_route('/api/new-version', NewVersion(new_version_checker))
    app.add_route('/api/execute/logs', ExecuteLogs(log_manager))
    app.add_route('/api/execute/logs/{execute_id}/details', ExecuteLogsDetails(log_manager))
    app.add_route('/api/execute/logs/current', ExecuteLogCurrent(log_manager))
    app.add_route('/api/execute/call', ExecuteCall(engine_runner))
    app.add_route('/api/challenge-logs', ChallengeLogs(settings_manager))
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
        playwright_timeout = 120000

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
                    self.playwright_timeout = parsed_config.get('playwright_timeout', self.db_path)
                except:
                    ex, val, tb = sys.exc_info()
                    warnings.warn('Error reading: {0}: {1} ({2}'.format(parsed_args.config, ex, val))

            env_debug = (os.environ.get('MONITORRENT_DEBUG', None) in ['true', 'True', '1'])

            self.debug = parsed_args.debug or env_debug or self.debug
            self.ip = parsed_args.ip or os.environ.get('MONITORRENT_IP', None) or self.ip
            self.port = parsed_args.port or try_int(os.environ.get('MONITORRENT_PORT', None)) or self.port
            self.db_path = parsed_args.db_path or os.environ.get('MONITORRENT_DB_PATH', None) or self.db_path
            self.playwright_timeout = parsed_args.playwright_timeout \
                                      or try_int(os.environ.get('MONITORRENT_PLAYWRIGHT_TIMEOUT', None)) \
                                      or self.playwright_timeout

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
    parser.add_argument('--playwright-timeout', type=int, dest='playwright_timeout',
                        help='Timeout for resolve Cloudflare challenge with Playwright (default {0})'.format(Config.playwright_timeout))

    parsed_args = parser.parse_args()
    config = Config(parsed_args)

    db_connection_string = "sqlite:///" + config.db_path

    init_db_engine(db_connection_string, False)
    load_plugins()
    upgrade()
    create_db()

    settings_manager = SettingsManager()
    tracker_manager = TrackersManager(settings_manager, get_plugins('tracker'), config)
    clients_manager = DbClientsManager(settings_manager, get_plugins('client'))
    notifier_manager = NotifierManager(settings_manager, get_plugins('notifier'))

    log_manager = ExecuteLogManager()
    engine_runner_logger = DbLoggerWrapper(log_manager, settings_manager)
    engine_runner = DBEngineRunner(engine_runner_logger, settings_manager, tracker_manager,
                                   clients_manager, notifier_manager)

    include_prerelease = settings_manager.get_new_version_check_include_prerelease()
    new_version_checker = NewVersionChecker(notifier_manager, include_prerelease)
    if settings_manager.get_is_new_version_checker_enabled():
        # noinspection PyBroadException
        try:
            new_version_checker.execute()
        except:
            pass
        new_version_checker.start(settings_manager.new_version_check_interval)

    debug = config.debug

    if debug:
        secret_key = 'Secret!'
        token = 'monitorrent'
    else:
        secret_key = os.urandom(24)
        token = ''.join(random.choice(string.ascii_letters) for _ in range(8))

    app = create_app(secret_key, token, tracker_manager, clients_manager, notifier_manager, settings_manager,
                     engine_runner, log_manager, new_version_checker)
    server_start_params = (config.ip, config.port)
    server = wsgi.Server(server_start_params, app)
    print('Server started on {0}:{1}'.format(*server_start_params))

    try:
        server.start()
    except KeyboardInterrupt:
        print('Stopping engine')
        engine_runner.stop()
        print('Stopping new_version_checker')
        new_version_checker.stop()
        server.stop()

    print('Server stopped')


if __name__ == '__main__':
    main()

