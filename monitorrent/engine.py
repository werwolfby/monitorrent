from builtins import str
from builtins import object
import sys
import threading

from queue import PriorityQueue
from collections import namedtuple
from datetime import datetime, timedelta

import pytz
import html

from sqlalchemy import Column, Integer, ForeignKey, Unicode, Enum, func
from monitorrent.db import Base, DBSession, row2dict, UTCDateTime
from monitorrent.utils.timers import timer

class Logger(object):
    def started(self, start_time):
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

    def add_torrent(self, filename, torrent, old_hash, topic_settings):
        """
        :type filename: str
        :type old_hash: str | None
        :type torrent: Torrent
        :type topic_settings: clients.TopicSettings | None
        :rtype: datetime
        """
        existing_torrent = self.find_torrent(torrent.info_hash)
        if existing_torrent:
            self.log.info(u"Torrent <b>%s</b> already added" % filename)
        elif self.clients_manager.add_torrent(torrent.raw_content, topic_settings):
            old_existing_torrent = self.find_torrent(old_hash) if old_hash else None
            if old_existing_torrent:
                self.log.info(u"Updated <b>%s</b>" % filename)
            else:
                self.log.info(u"Add new <b>%s</b>" % filename)
            if old_existing_torrent:
                if self.remove_torrent(old_hash):
                    self.log.info(u"Remove old torrent <b>%s</b>" %
                                  html.escape(old_existing_torrent['name']))
                else:
                    self.log.failed(u"Can't remove old torrent <b>%s</b>" %
                                    html.escape(old_existing_torrent['name']))
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
    last_execute = Column(UTCDateTime, nullable=True)


class Execute(Base):
    __tablename__ = 'execute'

    id = Column(Integer, primary_key=True)
    start_time = Column(UTCDateTime, nullable=False)
    finish_time = Column(UTCDateTime, nullable=False)
    status = Column(Enum('finished', 'failed'), nullable=False)
    failed_message = Column(Unicode, nullable=True)


class ExecuteLog(Base):
    __tablename__ = 'execute_log'

    id = Column(Integer, primary_key=True)
    execute_id = Column(ForeignKey('execute.id'))
    time = Column(UTCDateTime, nullable=False)
    message = Column(Unicode, nullable=False)
    level = Column(Enum('info', 'warning', 'failed', 'downloaded'), nullable=False)


class DbLoggerWrapper(Logger):
    def __init__(self, logger, log_manager, settings_manager=None):
        """
        :type logger: Logger | None
        :type log_manager: ExecuteLogManager
        :type settings_manager: SettingsManager | None
        """
        self._log_manager = log_manager
        self._logger = logger
        self._settings_manager = settings_manager

    def started(self, start_time):
        self._log_manager.started(start_time)
        if self._logger:
            self._logger.started(start_time)

    def finished(self, finish_time, exception):
        self._log_manager.finished(finish_time, exception)
        if self._logger:
            self._logger.finished(finish_time, exception)
        if self._settings_manager:
            self._log_manager.remove_old_entries(self._settings_manager.remove_logs_interval)

    def info(self, message):
        self._log_manager.log_entry(message, 'info')
        if self._logger:
            self._logger.info(message)

    def failed(self, message):
        self._log_manager.log_entry(message, 'failed')
        if self._logger:
            self._logger.failed(message)

    def downloaded(self, message, torrent):
        self._log_manager.log_entry(message, 'downloaded')
        if self._logger:
            self._logger.downloaded(message, torrent)


# noinspection PyMethodMayBeStatic
class ExecuteLogManager(object):
    _execute_id = None
    ongoing_progress_message = ""

    def __init__(self, notifier_manager):
        self.notifier_manager = notifier_manager

    def started(self, start_time):
        if self._execute_id is not None:
            raise Exception('Execute already in progress')

        with DBSession() as db:
            # default values for not finished execute is failed and finish_time equal to start_time
            execute = Execute(start_time=start_time, finish_time=start_time, status='failed')
            db.add(execute)
            db.commit()
            self._execute_id = execute.id
        self.notifier_manager.begin_execute(self.ongoing_progress_message)

    def finished(self, finish_time, exception):
        if self._execute_id is None:
            raise Exception('Execute is not started')

        with DBSession() as db:
            # noinspection PyArgumentList
            execute = db.query(Execute).filter(Execute.id == self._execute_id).first()
            execute.status = 'finished' if exception is None else 'failed'
            execute.finish_time = finish_time
            if exception is not None:
                execute.failed_message = html.escape(str(exception))
        self._execute_id = None
        self.notifier_manager.end_execute(self.ongoing_progress_message)

    def log_entry(self, message, level):
        if self._execute_id is None:
            raise Exception('Execute is not started')

        with DBSession() as db:
            execute_log = ExecuteLog(execute_id=self._execute_id, time=datetime.now(pytz.utc),
                                     message=message, level=level)
            db.add(execute_log)
        if level == 'downloaded' or level == 'failed':
            self.notifier_manager.topic_status_updated(self.ongoing_progress_message, message)

    def get_log_entries(self, skip, take):
        with DBSession() as db:
            downloaded_sub_query = db.query(ExecuteLog.execute_id, func.count(ExecuteLog.id).label('count')) \
                .group_by(ExecuteLog.execute_id, ExecuteLog.level) \
                .having(ExecuteLog.level == 'downloaded') \
                .subquery()
            failed_sub_query = db.query(ExecuteLog.execute_id, func.count(ExecuteLog.id).label('count')) \
                .group_by(ExecuteLog.execute_id, ExecuteLog.level) \
                .having(ExecuteLog.level == 'failed') \
                .subquery()

            result_query = db.query(Execute, downloaded_sub_query.c.count, failed_sub_query.c.count) \
                .outerjoin(failed_sub_query, Execute.id == failed_sub_query.c.execute_id) \
                .outerjoin(downloaded_sub_query, Execute.id == downloaded_sub_query.c.execute_id) \
                .order_by(Execute.finish_time.desc()) \
                .offset(skip) \
                .limit(take)

            result = []
            for execute, downloads, fails in result_query.all():
                execute_result = row2dict(execute)
                execute_result['downloaded'] = downloads or 0
                execute_result['failed'] = fails or 0
                execute_result['is_running'] = execute.id == self._execute_id
                result.append(execute_result)

            execute_count = db.query(func.count(Execute.id)).scalar()

        return result, execute_count

    def remove_old_entries(self, prune_days):
        # SELECT id FROM execute WHERE start_time <= datetime('now', '-10 days') ORDER BY id DESC LIMIT 1
        with DBSession() as db:
            prune_date = datetime.now(pytz.utc) - timedelta(days=prune_days)
            execute_id = db.query(Execute.id) \
                .filter(Execute.start_time <= prune_date) \
                .order_by(Execute.id.desc()) \
                .limit(1) \
                .scalar()

            if execute_id is not None:
                db.query(ExecuteLog) \
                    .filter(ExecuteLog.execute_id <= execute_id) \
                    .delete(synchronize_session=False)

                db.query(Execute) \
                    .filter(Execute.id <= execute_id) \
                    .delete(synchronize_session=False)

    def is_running(self, execute_id=None):
        if execute_id is not None:
            return self._execute_id == execute_id
        return self._execute_id is not None

    def get_execute_log_details(self, execute_id, after=None):
        with DBSession() as db:
            filters = [ExecuteLog.execute_id == execute_id]
            if after is not None:
                filters.append(ExecuteLog.id > after)
            log_entries = db.query(ExecuteLog).filter(*filters).all()
            return [row2dict(e) for e in log_entries]

    def get_current_execute_log_details(self, after=None):
        if self._execute_id is None:
            return None

        return self.get_execute_log_details(self._execute_id, after)


class EngineRunner(threading.Thread):
    RunMessage = namedtuple('RunMessage', ['priority', 'ids'])
    StopMessage = namedtuple('StopMessage', ['priority'])

    def __init__(self, logger, trackers_manager, clients_manager, **kwargs):
        """
        :type logger: Logger
        :type trackers_manager: plugin_managers.TrackersManager
        :type clients_manager: plugin_managers.ClientsManager
        """
        interval_param = kwargs.pop('interval', None)
        last_execute_param = kwargs.pop('last_execute', None)

        super(EngineRunner, self).__init__(**kwargs)
        self.logger = logger
        self.trackers_manager = trackers_manager
        self.clients_manager = clients_manager
        self.is_executing = False
        self.is_stoped = False
        self._interval = float(interval_param) if interval_param else 7200
        self._last_execute = last_execute_param
        self.message_box = PriorityQueue()

        self.timer_cancel = None
        self._create_timer()

        self.start()

    @property
    def interval(self):
        return self._interval

    @interval.setter
    def interval(self, value):
        self._interval = value
        self._create_timer()

    @property
    def last_execute(self):
        return self._last_execute

    @last_execute.setter
    def last_execute(self, value):
        self._last_execute = value

    # noinspection PyBroadException
    def run(self):
        while not self.is_stoped:
            msg = self._receive()

            if isinstance(msg, EngineRunner.StopMessage):
                self.is_stoped = True
                self.timer_cancel()
                return

            ids = msg.ids \
                if isinstance(msg, EngineRunner.RunMessage) \
                else None

            try:
                self._execute(ids=ids)
            except:
                pass

    def stop(self):
        self.message_box.put(EngineRunner._stop_message())

    def execute(self, ids):
        if not self.is_executing:
            msg = EngineRunner._run_message(ids=ids)
            self.message_box.put_nowait(msg)

    def _create_timer(self):
        def timer_fn():
            msg = EngineRunner._run_message()
            self.message_box.put_nowait(msg)

        if self.timer_cancel is not None:
            self.timer_cancel()

        self.timer_cancel = timer(self.interval, timer_fn)

    def _receive(self):
        return self.message_box.get(block=True)

    # noinspection PyBroadException
    def _execute(self, ids=None):
        caught_exception = None
        self.is_executing = True
        try:
            self.logger.started(datetime.now(pytz.utc))
            self.trackers_manager.execute(Engine(self.logger, self.clients_manager), ids)
        except:
            caught_exception = sys.exc_info()[0]
        finally:
            self.is_executing = False
            self.last_execute = datetime.now(pytz.utc)
            self.logger.finished(self.last_execute, caught_exception)
        return True

    @staticmethod
    def _run_message(ids=None):
        return EngineRunner.RunMessage(priority=1, ids=ids)

    @staticmethod
    def _stop_message():
        return EngineRunner.StopMessage(priority=0)


class DBEngineRunner(EngineRunner):
    DEFAULT_INTERVAL = 7200

    def __init__(self, logger, trackers_manager, clients_manager, **kwargs):
        """
        :type logger: Logger
        :type trackers_manager: plugin_managers.TrackersManager
        :type clients_manager: plugin_managers.ClientsManager
        """
        execute_settings = self._get_execute_settings()
        super(DBEngineRunner, self).__init__(logger,
                                             trackers_manager,
                                             clients_manager,
                                             interval=execute_settings.interval,
                                             last_execute=execute_settings.last_execute,
                                             **kwargs)

    @property
    def interval(self):
        return self._interval

    @interval.setter
    def interval(self, value):
        self._interval = value
        self._create_timer()
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
