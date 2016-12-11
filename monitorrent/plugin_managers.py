from builtins import str
from builtins import object
import os
import html
from monitorrent.db import DBSession, row2dict
from monitorrent.plugins import Topic, Status
from monitorrent.plugins.trackers import TrackerPluginBase, WithCredentialsMixin, TrackerSettings
from monitorrent.upgrade_manager import add_upgrade

plugins = dict()


def load_plugins(plugins_dir="plugins"):
    file_dir = os.path.dirname(os.path.realpath(__file__))
    for d, dirnames, files in os.walk(os.path.join(file_dir, plugins_dir)):
        d = d[len(file_dir) + 1:]
        for f in files:
            if not f.endswith('.py') or f == '__init__.py':
                continue
            module_name = os.path.join("monitorrent", d, f[:-3]).replace(os.path.sep, '.')
            __import__(module_name)


def register_plugin(type, name, instance, upgrade=None):
    if not upgrade:
        upgrade = getattr(instance, 'upgrade', None)
    if upgrade:
        add_upgrade(upgrade)
    plugins.setdefault(type, dict())[name] = instance


def get_plugins(type):
    return plugins.get(type, dict())


def get_all_plugins():
    return {name: plugin for key in list(plugins.keys()) for name, plugin in list(plugins[key].items())}


class TrackersManager(object):
    """
    :type trackers: dict[str, TrackerPluginBase]
    :type settings_manager: settings_manager.SettingsManager
    """

    def __init__(self, settings_manager, trackers=None):
        if trackers is None:
            trackers = get_plugins('tracker')
        self.trackers = trackers
        self.settings_manager = settings_manager

    def get_settings(self, name):
        tracker = self.get_tracker(name)
        if not isinstance(tracker, WithCredentialsMixin):
            return None
        return tracker.get_credentials()

    def set_settings(self, name, settings):
        tracker = self.get_tracker(name)
        if not isinstance(tracker, WithCredentialsMixin):
            return False
        tracker.update_credentials(settings)
        return True

    def check_connection(self, name):
        tracker = self.get_tracker(name)
        if not isinstance(tracker, WithCredentialsMixin):
            return False
        tracker_settings = self.settings_manager.tracker_settings
        # get_tracker returns PluginTrackerBase
        # noinspection PyUnresolvedReferences
        tracker.init(tracker_settings)
        return tracker.verify()

    def get_tracker(self, name):
        if name not in self.trackers:
            raise KeyError('Tracker {} not found'.format(name))
        return self.trackers[name]

    def get_tracker_by_id(self, id):
        with DBSession() as db:
            topic_type = db.query(Topic.type).filter(Topic.id == id).first()
            if topic_type is None:
                raise KeyError('Topic {} not found'.format(id))
        return self.get_tracker(topic_type[0])

    def get_status_topics_ids(self, statuses):
        with DBSession() as db:
            ids = [res.id for res in db.query(Topic.id).filter(Topic.status.in_(statuses))]
            return ids

    def get_tracker_topics(self, name):
        tracker = self.get_tracker(name)
        return tracker.get_topics(None)

    def prepare_add_topic(self, url):
        tracker_settings = self.settings_manager.tracker_settings
        for tracker in list(self.trackers.values()):
            tracker.init(tracker_settings)
            parsed_url = tracker.prepare_add_topic(url)
            if parsed_url:
                return {'form': tracker.topic_form, 'settings': parsed_url}
        return None

    def add_topic(self, url, params):
        tracker_settings = self.settings_manager.tracker_settings
        for name, tracker in list(self.trackers.items()):
            tracker.init(tracker_settings)
            if not tracker.can_parse_url(url):
                continue
            if tracker.add_topic(url, params):
                return True
        return False

    def remove_topic(self, id):
        with DBSession() as db:
            topic = db.query(Topic).filter(Topic.id == id).first()
            if topic is None:
                raise KeyError('Topic {} not found'.format(id))
            db.delete(topic)
        return True

    def get_topic(self, id):
        tracker = self.get_tracker_by_id(id)
        settings = tracker.get_topic(id)
        form = tracker.topic_edit_form if hasattr(tracker, 'topic_edit_form') else tracker.topic_form
        return {'form': form, 'settings': settings}

    def update_topic(self, id, settings):
        tracker = self.get_tracker_by_id(id)
        return tracker.update_topic(id, settings)

    def reset_topic_status(self, id):
        with DBSession() as db:
            topic = db.query(Topic).filter(Topic.id == id).first()
            if topic is None:
                raise KeyError('Topic {} not found'.format(id))
            topic.status = Status.Ok
        return True

    def set_topic_paused(self, id, paused):
        with DBSession() as db:
            topic = db.query(Topic).filter(Topic.id == id).first()
            if topic is None:
                raise KeyError('Topic {} not found'.format(id))
            topic.paused = paused
        return True

    def get_watching_topics(self):
        watching_topics = []
        with DBSession() as db:
            dbtopics = db.query(Topic).all()
            for dbtopic in dbtopics:
                try:
                    tracker = self.get_tracker(dbtopic.type)
                except KeyError:
                    # TODO: Log warning of not existing topic
                    #       Need to think, should we return not existing plugin
                    #       as just default topic, and show it disabled on UI to
                    #       let user ability for delete such topics
                    continue
                topic = row2dict(dbtopic, None, ['id', 'url', 'display_name', 'last_update', 'paused'])
                topic['info'] = tracker.get_topic_info(dbtopic)
                topic['tracker'] = dbtopic.type
                topic['status'] = dbtopic.status.__str__()
                watching_topics.append(topic)
        return watching_topics

    def execute(self, engine, ids):
        tracker_settings = self.settings_manager.tracker_settings
        for name, tracker in list(self.trackers.items()):
            tracker.init(tracker_settings)
            try:
                topics = tracker.get_topics(ids)
                if len(topics) > 0:
                    engine.log.info(u"Start checking for <b>{}</b>".format(name))
                    tracker.execute(topics, engine)
                    engine.log.info(u"End checking for <b>{}</b>".format(name))
            except Exception as e:
                engine.log.failed(u"Failed while checking for <b>{0}</b>.\nReason: {1}"
                                  .format(name, html.escape(str(e))))


class ClientsManager(object):
    def __init__(self, clients=None, default_client_name=None):
        if clients is None:
            clients = get_plugins('client')
        self.clients = clients
        self.default_client = self.__get_default_client(default_client_name,
                                                        list(self.clients.values())[0] if len(self.clients) > 0 else None)

    def set_default(self, name):
        default_client = self.__get_default_client(name)
        if default_client is None:
            raise KeyError()
        self.default_client = default_client

    def get_default(self):
        return self.default_client

    def get_settings(self, name):
        client = self.get_client(name)
        return client.get_settings()

    def set_settings(self, name, settings):
        client = self.get_client(name)
        client.set_settings(settings)

    def check_connection(self, name):
        client = self.get_client(name)
        return client.check_connection()

    def get_client(self, name):
        return self.clients[name]

    def find_torrent(self, torrent_hash):
        if self.default_client is None:
            return False
        result = self.default_client.find_torrent(torrent_hash)
        return result or False

    def add_torrent(self, torrent, topic_settings):
        """
        :type topic_settings: clients.TopicSettings
        """
        if self.default_client is None:
            return False
        return self.default_client.add_torrent(torrent)

    def remove_torrent(self, torrent_hash):
        if self.default_client is None:
            return False
        return self.default_client.remove_torrent(torrent_hash)

    def __get_default_client(self, name=None, default=None):
        if name is not None:
            return self.clients.get(name, default)
        return default


class NotifierManager(object):
    def __init__(self, notifiers=None):
        if notifiers is None:
            notifiers = get_plugins('notifier')
        self.notifiers = notifiers

    def get_notifier(self, name):
        notifier = self.notifiers[name]
        return {'notifier': notifier, 'form': notifier.form}

    def send_test_message(self, name):
        notifier = self.get_notifier(name).get('notifier')
        return notifier.notify("Test Message", "This is monitorrent test message",
                               "https://github.com/werwolfby/monitorrent")

    def get_settings(self, name):
        notifier = self.get_notifier(name).get('notifier')
        return notifier.get_settings()

    def update_settings(self, name, settings):
        notifier = self.get_notifier(name).get('notifier')
        return notifier.update_settings(settings)

    def get_enabled(self, name):
        settings = self.get_settings(name)
        if settings is None:
            return False
        return settings.is_enabled

    def set_enabled(self, name, value):
        settings = self.get_settings(name)
        if settings is None:
            settings = self.get_notifier(name).get('notifier').settings_class()
        settings.is_enabled = value
        return self.update_settings(name, settings)


class DbClientsManager(ClientsManager):
    def __init__(self, clients, settings_manager):
        """
        :type clients: dict
        :type settings_manager: SettingsManager
        """
        self.settings_manager = settings_manager
        super(DbClientsManager, self).__init__(clients, settings_manager.get_default_client())

    def set_default(self, name):
        self.settings_manager.set_default_client(name)
        super(DbClientsManager, self).set_default(name)
