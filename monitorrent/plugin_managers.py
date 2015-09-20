import os
from monitorrent.db import DBSession, row2dict
from monitorrent.plugins import Topic
from monitorrent.plugins.trackers import TrackerPluginBase, WithCredentialsMixin

plugins = dict()
upgrades = list()


def load_plugins(plugins_dir="plugins"):
    file_dir = os.path.dirname(os.path.realpath(__file__))
    for d, dirnames, files in os.walk(os.path.join(file_dir, plugins_dir)):
        d = d[len(file_dir)+1:]
        for f in files:
            if not f.endswith('.py') or f == '__init__.py':
                continue
            module_name = os.path.join("monitorrent", d, f[:-3]).replace(os.path.sep, '.')
            __import__(module_name)


def register_plugin(type, name, instance, upgrade=None):
    if not upgrade:
        upgrade = getattr(instance, 'upgrade', None)
    if upgrade:
        upgrades.append(upgrade)
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
        if not tracker or not isinstance(tracker, WithCredentialsMixin):
            return False
        return tracker.verify()

    def get_tracker(self, name):
        return self.trackers[name]

    def get_tracker_by_id(self, id):
        with DBSession() as db:
            topic_type = db.query(Topic.type).filter(Topic.id == id).first()
            if topic_type is None:
                raise KeyError('Topic {} not found'.format(id))
        return self.get_tracker(topic_type[0])

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
                topic = row2dict(dbtopic, None, ['id', 'url', 'display_name', 'last_update'])
                topic['info'] = tracker.get_topic_info(dbtopic)
                topic['tracker'] = dbtopic.type
                watching_topics.append(topic)
        return watching_topics

    def execute(self, engine):
        for name, tracker in self.trackers.iteritems():
            try:
                engine.log.info("Start checking for <b>{}</b>".format(name))
                tracker.execute(None, engine)
                engine.log.info("End checking for <b>{}</b>".format(name))
            except Exception as e:
                engine.log.failed("Failed while checking for <b>{0}</b>.\nReason: {1}".format(name, e.message))


class ClientsManager(object):
    def __init__(self, clients=None):
        if clients is None:
            clients = get_plugins('client')
        self.clients = clients

    def get_settings(self, name):
        client = self.get_client(name)
        return client.get_settings()

    def set_settings(self, name, settings):
        client = self.get_client(name)
        return client.set_settings(settings)

    def check_connection(self, name):
        client = self.get_client(name)
        return client.check_connection()

    def get_client(self, name):
        return self.clients[name]

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
