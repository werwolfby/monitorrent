import threading


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

    def find_torrent(self, torrent_hash):
        return self.clients_manager.find_torrent(torrent_hash)

    def add_torrent(self, torrent):
        return self.clients_manager.add_torrent(torrent)

    def remove_torrent(self, torrent_hash):
        return self.clients_manager.remove_torrent(torrent_hash)


class EngineRunner(object):
    def __init__(self, logger, trackers_manager, clients_manager, interval=7200):
        """
        :type logger: Logger
        :type trackers_manager: plugin_managers.TrackersManager
        :type clients_manager: plugin_managers.ClientsManager
        :type interval: int
        """
        self.logger = logger
        self.trackers_manager = trackers_manager
        self.clients_manager = clients_manager
        self._interval = interval
        self._execute_lock = threading.RLock()
        self._is_executing = False
        self.timer = threading.Timer(self._interval, self._run)
        self._timer_lock = threading.RLock()

    @property
    def is_executing(self):
        with self._execute_lock:
            return self._is_executing

    @property
    def interval(self):
        return self._interval

    @interval.setter
    def interval(self, value):
        self._interval = value
        self.timer.cancel()
        with self._timer_lock:
            self.timer = threading.Timer(self._interval, self._run)
            self.timer.start()

    def start(self):
        self.timer.start()

    def stop(self):
        self.timer.cancel()

    def execute(self):
        with self._execute_lock:
            if self._is_executing:
                return False
            self._is_executing = True
        self.trackers_manager.execute(Engine(self.logger, self.clients_manager))
        with self._execute_lock:
            self._is_executing = False
        return True

    def _run(self):
        with self._timer_lock:
            old_timer = self.timer
        try:
            self.execute()
        finally:
            with self._timer_lock:
                # if timer was changed by update interval property
                # do not restart the timer
                if self.timer == old_timer:
                    self.timer = threading.Timer(self._interval, self._run)
                    self.timer.start()
