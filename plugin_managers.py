from path import path
from db import DBSession, row2dict
from plugins import Topic
from plugins.trackers import TrackerPluginBase, TrackerPluginWithCredentialsBase

plugins = dict()
upgrades = dict()


def load_plugins(plugin_folder="plugins"):
    p = path(plugin_folder)
    for f in p.walk("*.py"):
        if f.basename() == "__init__.py":
            continue
        plugin_subpackages = filter(None, f.parent.splitall())
        module_name = '.'.join(plugin_subpackages + [f.namebase])
        __import__(module_name)


def register_plugin(type, name, instance, upgrade=None):
    if not upgrade:
        upgrade = getattr(instance, 'upgrade', None)
    if upgrade:
        upgrades[name] = upgrade
    plugins.setdefault(type, dict())[name] = instance


def get_plugins(type):
    return plugins.get(type, dict())


def get_all_plugins():
    return {name: plugin for key in plugins.keys() for name, plugin in plugins[key].items()}


class TrackersManager(object):
    """
    :type trackers: dict[str, TrackerPluginBase]
    """
    def __init__(self):
        self.trackers = get_plugins('tracker')

    def get_settings(self, name):
        tracker = self.get_tracker(name)
        if not tracker or not isinstance(tracker, TrackerPluginWithCredentialsBase):
            return None
        return tracker.get_credentials()

    def set_settings(self, name, settings):
        tracker = self.get_tracker(name)
        if not tracker or not isinstance(tracker, TrackerPluginWithCredentialsBase):
            return False
        tracker.update_credentials(settings)
        return True

    def check_connection(self, name):
        tracker = self.get_tracker(name)
        if not tracker or not isinstance(tracker, TrackerPluginWithCredentialsBase):
            return False
        return tracker.verify()

    def get_tracker(self, name):
        return self.trackers.get(name)

    def prepare_add_topic(self, url):
        for tracker in self.trackers.values():
            parsed_url = tracker.prepare_add_topic(url)
            if parsed_url:
                return {'form': tracker.topic_form, 'settings': parsed_url}
        return None

    def add_topic(self, url, params):
        for name, tracker in self.trackers.items():
            if not tracker.can_parse_url(url):
                continue
            if tracker.add_topic(url, params):
                return True
        return False

    def remove_topic(self, id):
        with DBSession() as db:
            topic = db.query(Topic).filter(Topic.id == id).first()
            if topic is None:
                return False
            db.delete(topic)
        return True

    def get_topic(self, id):
        with DBSession() as db:
            topic = db.query(Topic).filter(Topic.id == id).first()
            if topic is None:
                return None
            name = topic.type
        tracker = self.get_tracker(name)
        if tracker is None:
            return None
        settings = tracker.get_topic(id)
        form = tracker.topic_edit_form if hasattr(tracker, 'topic_edit_form') else tracker.topic_form
        return {'form': form, 'settings': settings}

    def update_watch(self, id, settings):
        with DBSession() as db:
            topic = db.query(Topic).filter(Topic.id == id).first()
            if topic is None:
                return False
            name = topic.type
        tracker = self.get_tracker(name)
        if tracker is None:
            return False
        return tracker.update_topic(id, settings)

    def get_watching_torrents(self):
        watching_torrents = []
        with DBSession() as db:
            dbtopics = db.query(Topic).all()
            for dbtopic in dbtopics:
                tracker = self.get_tracker(dbtopic.type)
                if not tracker:
                    continue
                topic = row2dict(dbtopic, None, ['id', 'url', 'display_name', 'last_update'])
                topic['info'] = tracker.get_topic_info(dbtopic)
                topic['tracker'] = dbtopic.type
                watching_torrents.append(topic)
        return watching_torrents

    def execute(self, progress_reporter=lambda m: None):
        for tracker in self.trackers:
            tracker.execute(progress_reporter)


class ClientsManager(object):
    def __init__(self):
        self.clients = get_plugins('client')

    def get_settings(self, name):
        client = self.get_client(name)
        if not client:
            return None
        return client.get_settings()

    def set_settings(self, name, settings):
        client = self.get_client(name)
        if not client:
            return False
        client.set_settings(settings)
        return True

    def check_connection(self, name):
        client = self.get_client(name)
        if not client:
            return False
        return client.check_connection()

    def get_client(self, name):
        clients = filter(lambda c: c.name == name, self.clients)
        if len(clients) != 1:
            return None
        return clients[0]

    def find_torrent(self, torrent_hash):
        for client in self.clients:
            result = client.find_torrent(torrent_hash)
            if result:
                return result
        return False

    def add_torrent(self, torrent):
        for client in self.clients:
            if client.add_torrent(torrent):
                return True
        return False

    def remove_torrent(self, torrent_hash):
        for client in self.clients:
            if client.remove_torrent(torrent_hash):
                return True
        return False
