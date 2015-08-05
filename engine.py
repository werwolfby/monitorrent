import threading
from datetime import datetime
from sqlalchemy import Column, Integer, DateTime
from db import Base, DBSession


class Logger(object):
    def started(self):
        pass

    def finished(self, finish_time, exception):
        pass

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

    def add_torrent(self, filename, torrent, old_hash):
        """
        :type filename: str
        :type old_hash: str | None
        :type torrent: Torrent
        :rtype: datetime
        """
        existing_torrent = self.find_torrent(torrent.info_hash)
        if existing_torrent:
            self.log.info(u"Torrent <b>%s</b> already added" % filename)
        elif self.clients_manager.add_torrent(torrent.raw_content):
            old_existing_torrent = self.find_torrent(old_hash) if old_hash else None
            if old_existing_torrent:
                self.log.info(u"Updated <b>%s</b>" % filename)
            else:
                self.log.info(u"Add new <b>%s</b>" % filename)
            if old_existing_torrent:
                if self.remove_torrent(old_hash):
                    self.log.info(u"Remove old torrent <b>%s</b>" %
                                  old_existing_torrent['name'])
                else:
                    self.log.failed(u"Can't remove old torrent <b>%s</b>" %
                                    old_existing_torrent['name'])
            existing_torrent = self.find_torrent(torrent.info_hash)
        if existing_torrent:
            last_update = existing_torrent['date_added']
        else:
            last_update = datetime.now()
        return last_update

    def remove_torrent(self, torrent_hash):
        return self.clients_manager.remove_torrent(torrent_hash)


class Execute(Base):
    __tablename__ = "settings_execute"

    id = Column(Integer, primary_key=True)
    interval = Column(Integer, nullable=False)
    last_execute = Column(DateTime, nullable=True)


class EngineRunner(object):
    def __init__(self, logger, trackers_manager, clients_manager):
        """
        :type logger: Logger
        :type trackers_manager: plugin_managers.TrackersManager
        :type clients_manager: plugin_managers.ClientsManager
        """
        self.logger = logger
        self.trackers_manager = trackers_manager
        self.clients_manager = clients_manager
        self._execute_lock = threading.RLock()
        self._is_executing = False
        self.timer = threading.Timer(self.interval, self._run)
        self.timer.start()
        self._timer_lock = threading.RLock()

    @property
    def is_executing(self):
        with self._execute_lock:
            return self._is_executing

    @property
    def interval(self):
        settings_execute = self._get_settings_execute()
        return settings_execute.interval

    @interval.setter
    def interval(self, value):
        settings_execute = self._get_settings_execute()
        with DBSession() as db:
            db.add(settings_execute)
            settings_execute.interval = value
            db.commit()
        self.timer.cancel()
        with self._timer_lock:
            self.timer = threading.Timer(value, self._run)
            self.timer.start()

    @property
    def last_execute(self):
        settings_execute = self._get_settings_execute()
        return settings_execute.last_execute

    def start(self):
        self.timer.start()

    def stop(self):
        self.timer.cancel()

    def execute(self):
        caught_exception = None
        with self._execute_lock:
            if self._is_executing:
                return False
            self._is_executing = True
        try:
            self.logger.started()
            self.trackers_manager.execute(Engine(self.logger, self.clients_manager))
        except Exception as e:
            caught_exception = e
        finally:
            with self._execute_lock:
                self._is_executing = False
            finish_time = datetime.now()
            self.logger.finished(finish_time, caught_exception)
            self._set_last_execute(finish_time)
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
                    self.timer = threading.Timer(self.interval, self._run)
                    self.timer.start()

    def _set_last_execute(self, value):
        settings_execute = self._get_settings_execute()
        with DBSession() as db:
            db.add(settings_execute)
            settings_execute.last_execute = value
            db.commit()

    @staticmethod
    def _get_settings_execute():
        with DBSession() as db:
            if db.query(Execute).count() == 0:
                settings_execute = Execute(interval=7200, last_execute=None)
                db.add(settings_execute)
                db.commit()
            settings_execute = db.query(Execute).first()
            db.expunge(settings_execute)
        return settings_execute
