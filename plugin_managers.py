from path import path

plugins = dict()

def load_plugins(plugin_folder="plugins"):
    p = path(plugin_folder)
    for f in p.walk("*.py"):
        if f.basename() == "__init__.py":
            continue
        plugin_subpackages = filter(None, f.parent.splitall())
        module_name = '.'.join(plugin_subpackages + [f.namebase])
        __import__(module_name)

def register_plugin(type, name, instance):
    plugins.setdefault(type, dict())[name] = instance

def get_plugins(type):
    return plugins.get(type, dict()).values()


class TrackersManager(object):
    def __init__(self):
        self.trackers = get_plugins('tracker')

    def parse_url(self, url):
        for tracker in self.trackers:
            name = tracker.parse_url(url)
            if name:
                return name
        return None

    def add_watch(self, url):
        for tracker in self.trackers:
            if tracker.add_watch(url):
                return True
        return False

    def remove_watch(self, url):
        for tracker in self.trackers:
            if tracker.remove_watch(url) > 0:
                return True
        return False

    def get_watching_torrents(self):
        watching_torrents = []
        for tracker in self.trackers:
            torrents = tracker.get_watching_torrents()
            for torrent in torrents:
                adding_torrents = dict(torrent)
                adding_torrents['tracker'] = tracker.name
                watching_torrents.append(adding_torrents)
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
