class Logger(object):
    def info(self, message):
        pass

    def failed(self, message):
        pass

    def downloaded(self, message, torrent):
        pass


class Engine(object):
    def __init__(self, logger, clients_manager):
        """

        :type logger: Logger
        :type clients_manager: plugin_managers.ClientsManager
        """
        self.log = logger
        self.clients_manager = clients_manager

    def add_torrent(self, torrent):
        #return False
        return self.clients_manager.add_torrent(torrent)

    def remove_torrent(self, torrent_hash):
        #return False
        return self.clients_manager.remove_torrent(torrent_hash)
