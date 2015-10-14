import threading
from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, ForeignKey, Unicode, Enum, func
from db import row2dict
from monitorrent.db import Base, DBSession


class Logger(object):
    def started(self):
        """
        """

    def finished(self, finish_time, exception):
        """
        """

    def info(self, message):
        """
        """

    def failed(self, message):
        """
        """

    def downloaded(self, message, torrent):
        """
        """


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
        if not existing_torrent:
            raise Exception('Torrent {0} wasn\'t added'.format(filename))
        return existing_torrent['date_added']

    def remove_torrent(self, torrent_hash):
        return self.clients_manager.remove_torrent(torrent_hash)


class ExecuteSettings(Base):
    __tablename__ = "settings_execute"

    id = Column(Integer, primary_key=True)
    interval = Column(Integer, nullable=False)
    last_execute = Column(DateTime, nullable=True)


class Execute(Base):
    __tablename__ = 'execute'

    id = Column(Integer, primary_key=True)
    start_time = Column(DateTime, nullable=False)
    finish_time = Column(DateTime, nullable=False)
    status = Column(Enum('finished', 'failed'), nullable=False)
    failed_message = Column(Unicode, nullable=True)


class ExecuteLog(Base):
    __tablename__ = 'execute_log'

    id = Column(Integer, primary_key=True)
    execute_id = Column(ForeignKey('execute.id'))
    time = Column(DateTime, nullable=False)
    message = Column(Unicode, nullable=False)
    level = Column(Enum('info', 'warning', 'failed', 'downloaded'), nullable=False)


class DbLoggerWrapper(Logger):
    _logger = None

    def __init__(self, logger, log_manager):
        """
        :type logger: Logger
        :type log_manager: ExecuteLogManager
        """
        self._log_manager = log_manager
        self._logger = logger

    def started(self):
        self._log_manager.started()
        self._logger.started()

    def finished(self, finish_time, exception):
        self._log_manager.finished(finish_time, exception)
        self._logger.finished(finish_time, exception)

    def info(self, message):
        self._log_manager.log_entry(message, 'info')
        self._logger.info(message)

    def failed(self, message):
        self._log_manager.log_entry(message, 'failed')
        self._logger.failed(message)

    def downloaded(self, message, torrent):
        self._log_manager.log_entry(message, 'downloaded')
        self._logger.downloaded(message, torrent)


# noinspection PyMethodMayBeStatic
class ExecuteLogManager(object):
    _execute_id = None

    def started(self):
        if self._execute_id is not None:
            raise Exception('Execute already in progress')

        with DBSession() as db:
            # noinspection PyArgumentList
            start_time = datetime.now()
            # default values for not finished execute is failed and finish_time equal to start_time
            execute = Execute(start_time=start_time, finish_time=start_time, status='failed')
            db.add(execute)
            db.commit()
            self._execute_id = execute.id

    def finished(self, finish_time, exception):
        if self._execute_id is None:
            raise Exception('Execute is not started')

        with DBSession() as db:
            # noinspection PyArgumentList
            execute = db.query(Execute).filter(Execute.id == self._execute_id).first()
            execute.status = 'finished' if exception is None else 'failed'
            execute.finish_time = finish_time
            if exception is not None:
                execute.failed_message = unicode(exception)
        self._execute_id = None

    def log_entry(self, message, level):
        if self._execute_id is None:
            raise Exception('Execute is not started')

        with DBSession() as db:
            execute_log = ExecuteLog(execute_id=self._execute_id, time=datetime.now(),
                                     message=message, level=level)
            db.add(execute_log)

    def get_log_entries(self, skip, take):
        with DBSession() as db:
            downloaded_sub_query = db.query(ExecuteLog.execute_id, func.count(ExecuteLog.id).label('count'))\
                .group_by(ExecuteLog.execute_id, ExecuteLog.level)\
                .having(ExecuteLog.level == 'downloaded')\
                .subquery()
            failed_sub_query = db.query(ExecuteLog.execute_id, func.count(ExecuteLog.id).label('count'))\
                .group_by(ExecuteLog.execute_id, ExecuteLog.level)\
                .having(ExecuteLog.level == 'failed')\
                .subquery()

            result_query = db.query(Execute, downloaded_sub_query.c.count, failed_sub_query.c.count)\
                .outerjoin(failed_sub_query, Execute.id == failed_sub_query.c.execute_id)\
                .outerjoin(downloaded_sub_query, Execute.id == downloaded_sub_query.c.execute_id)\
                .order_by(Execute.finish_time.desc())\
                .offset(skip)\
                .limit(take)

            result = []
            for execute, downloads, fails in result_query.all():
                execute_result = row2dict(execute)
                execute_result['downloaded'] = downloads or 0
                execute_result['failed'] = fails or 0
                result.append(execute_result)

            execute_count = db.query(func.count(Execute.id)).scalar()

        return result, execute_count


class EngineRunner(threading.Thread):
    def __init__(self, logger, trackers_manager, clients_manager, **kwargs):
        """
        :type logger: Logger
        :type trackers_manager: plugin_managers.TrackersManager
        :type clients_manager: plugin_managers.ClientsManager
        """
        interval_param = kwargs.pop('interval', None)
        super(EngineRunner, self).__init__(**kwargs)
        self.logger = logger
        self.trackers_manager = trackers_manager
        self.clients_manager = clients_manager
        self.waiter = threading.Event()
        self.is_executing = False
        self.is_stoped = False
        self._interval = float(interval_param) if interval_param else 7200
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
    DEFAULT_INTERVAL = 7200

    def __init__(self, logger, trackers_manager, clients_manager, **kwargs):
        """
        :type logger: Logger
        :type trackers_manager: plugin_managers.TrackersManager
        :type clients_manager: plugin_managers.ClientsManager
        """
        super(DBEngineRunner, self).__init__(logger, trackers_manager, clients_manager, **kwargs)
        execute_settings = self._get_execute_settings()
        self._interval = execute_settings.interval
        self._last_execute = execute_settings.last_execute

    @property
    def interval(self):
        return self._interval

    @interval.setter
    def interval(self, value):
        self._interval = value
        self._update_execute_settings()

    @property
    def last_execute(self):
        return self._last_execute

    @last_execute.setter
    def last_execute(self, value):
        self._last_execute = value
        self._update_execute_settings()

    def _update_execute_settings(self):
        with DBSession() as db:
            settings_execute = db.query(ExecuteSettings).first()
            if not settings_execute:
                settings_execute = ExecuteSettings()
                db.add(settings_execute)
            settings_execute.interval = self._interval
            settings_execute.last_execute = self._last_execute

    def _get_execute_settings(self):
        with DBSession() as db:
            settings_execute = db.query(ExecuteSettings).first()
            if not settings_execute:
                settings_execute = ExecuteSettings(interval=self.DEFAULT_INTERVAL, last_execute=None)
            else:
                db.expunge(settings_execute)
        return settings_execute
