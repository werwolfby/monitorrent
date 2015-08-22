from path import path
from monitorrent.db import DBSession, row2dict
from monitorrent.plugins import Topic
from monitorrent.plugins.trackers import TrackerPluginBase, TrackerPluginWithCredentialsBase

plugins = dict()
upgrades = dict()


def load_plugins(plugin_folder="monitorrent//plugins"):
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
    :type trackers: dict[str, TrackerPluginBase | TrackerPluginWithCredentialsBase]
    """
    def __init__(self, trackers=None):
        if trackers is None:
            trackers = get_plugins('tracker')
        self.trackers = trackers

    def get_settings(self, name):
        tracker = self.get_tracker(name)
        if not isinstance(tracker, TrackerPluginWithCredentialsBase):
            return None
        return tracker.get_credentials()

    def set_settings(self, name, settings):
        tracker = self.get_tracker(name)
        if not isinstance(tracker, TrackerPluginWithCredentialsBase):
            return False
        tracker.update_credentials(settings)
        return True

    def check_connection(self, name):
        tracker = self.get_tracker(name)
        if not tracker or not isinstance(tracker, TrackerPluginWithCredentialsBase):
            return False
        return tracker.verify()

    def get_tracker(self, name):
        return self.trackers[name]

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
                raise KeyError('Topic {} not found'.format(id))
            name = topic.type
        tracker = self.get_tracker(name)
        if tracker is None:
            raise KeyError('Can\'t find plugin {0} for topic {1}'.format(name, id))
        settings = tracker.get_topic(id)
        form = tracker.topic_edit_form if hasattr(tracker, 'topic_edit_form') else tracker.topic_form
        return {'form': form, 'settings': settings}

    def update_watch(self, id, settings):
        with DBSession() as db:
            topic = db.query(Topic).filter(Topic.id == id).first()
            if topic is None:
                raise KeyError('Topic {} not found'.format(id))
            name = topic.type
        tracker = self.get_tracker(name)
        if tracker is None:
            raise KeyError('Can\'t find plugin {0} for topic {1}'.format(name, id))
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

    def execute(self, engine):
        for name, tracker in self.trackers.iteritems():
            try:
                engine.log.info("Start checking for <b>{}</b>".format(name))
                tracker.execute(None, engine)
                engine.log.info("End checking for <b>{}</b>".format(name))
            except Exception as e:
                engine.log.info("Failed while checking for <b>{0}</b>.\nReason: {1}".format(name, e.message))


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
        return self.clients.get(name)

    def find_torrent(self, torrent_hash):
        for name, client in self.clients.iteritems():
            result = client.find_torrent(torrent_hash)
            if result:
                return result
        return False

    def add_torrent(self, torrent):
        for name, client in self.clients.iteritems():
            if client.add_torrent(torrent):
                return True
        return False

    def remove_torrent(self, torrent_hash):
        for name, client in self.clients.iteritems():
            if client.remove_torrent(torrent_hash):
                return True
        return False
