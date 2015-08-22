import threading
from datetime import datetime
from sqlalchemy import Column, Integer, DateTime
from monitorrent.db import Base, DBSession


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


class EngineRunner(threading.Thread):
    def __init__(self, logger, trackers_manager, clients_manager, **kwargs):
        """
        :type logger: Logger
        :type trackers_manager: plugin_managers.TrackersManager
        :type clients_manager: plugin_managers.ClientsManager
        """
        super(EngineRunner, self).__init__(**kwargs)
        self.logger = logger
        self.trackers_manager = trackers_manager
        self.clients_manager = clients_manager
        self.waiter = threading.Event()
        self.is_executing = False
        self.is_stoped = False
        self._interval = 7200
        self._last_execute = None
        self.start()

    @property
    def interval(self):
        return self._interval

    @interval.setter
    def interval(self, value):
        self._interval = value

    @property
    def last_execute(self):
        return self._last_execute

    @last_execute.setter
    def last_execute(self, value):
        self._last_execute = value

    def run(self):
        while not self.is_stoped:
            self.waiter.wait(self.interval)
            if self.is_stoped:
                return
            self._execute()
            self.waiter.clear()

    def stop(self):
        self.is_stoped = True
        self.waiter.set()

    def execute(self):
        self.waiter.set()

    def _execute(self):
        caught_exception = None
        self.is_executing = True
        try:
            self.logger.started()
            self.trackers_manager.execute(Engine(self.logger, self.clients_manager))
        except Exception as e:
            caught_exception = e
        finally:
            self.is_executing = False
            self.last_execute = datetime.now()
            self.logger.finished(self.last_execute, caught_exception)
        return True


class DBEngineRunner(EngineRunner):
    def __init__(self, logger, trackers_manager, clients_manager, **kwargs):
        """
        :type logger: Logger
        :type trackers_manager: plugin_managers.TrackersManager
        :type clients_manager: plugin_managers.ClientsManager
        """
        super(DBEngineRunner, self).__init__(logger, trackers_manager, clients_manager, **kwargs)

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

    @property
    def last_execute(self):
        settings_execute = self._get_settings_execute()
        return settings_execute.last_execute

    @last_execute.setter
    def last_execute(self, value):
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
