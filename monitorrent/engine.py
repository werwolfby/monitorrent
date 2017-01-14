import sys
import six
import threading
import traceback

from queue import PriorityQueue
from collections import namedtuple
from datetime import datetime, timedelta

import pytz
import html

from sqlalchemy import Column, Integer, ForeignKey, Unicode, Enum, func
from monitorrent.db import Base, DBSession, row2dict, UTCDateTime
from monitorrent.utils.timers import timer
from monitorrent.plugins.status import Status


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

    def failed(self, message, exc_type=None, exc_value=None, exc_tb=None):
        """
        """

    def downloaded(self, message, torrent):
        """
        """


def _clamp(value, min_value=0, max_value=100):
    return max(min_value, min(value, max_value))


class Engine(object):
    def __init__(self, logger, settings_manager, trackers_manager, clients_manager, notifier_manager):
        """
        :type logger: Logger
        :type settings_manager: settings_manager.SettingsManager
        :type trackers_manager: plugin_managers.TrackersManager
        :type clients_manager: plugin_managers.ClientsManager
        :type notifier_manager: plugin_managers.NotifierManager
        """
        self.log = logger
        self.settings_manager = settings_manager
        self.trackers_manager = trackers_manager
        self.clients_manager = clients_manager
        self.notifier_manager = notifier_manager

    def info(self, message):
        self.log.info(message)

    def failed(self, message, exc_type=None, exc_value=None, exc_tb=None):
        self.log.failed(message, exc_type, exc_value, exc_tb)

    def downloaded(self, message, torrent):
        self.log.downloaded(message, torrent)

    def update_progress(self, progress):
        pass

    def start(self, trackers_count, notifier_manager_execute):
        return EngineTrackers(trackers_count, notifier_manager_execute, self)

    def add_torrent(self, filename, torrent, old_hash, topic_settings):
        """
        :type filename: str
        :type old_hash: str | None
        :type torrent: Torrent
        :type topic_settings: clients.TopicSettings | None
        :rtype: datetime
        """
        existing_torrent = self.clients_manager.find_torrent(torrent.info_hash)
        if existing_torrent:
            self.info(u"Torrent <b>{0}</b> already added".format(filename))
        elif self.clients_manager.add_torrent(torrent.raw_content, topic_settings):
            old_existing_torrent = self.clients_manager.find_torrent(old_hash) if old_hash else None
            if old_existing_torrent:
                self.info(u"Updated <b>{0}</b>".format(filename))
            else:
                self.info(u"Add new <b>{0}</b>".format(filename))
            if old_existing_torrent:
                if self.clients_manager.remove_torrent(old_hash):
                    self.info(u"Remove old torrent <b>{0}</b>"
                              .format(html.escape(old_existing_torrent['name'])))
                else:
                    self.failed(u"Can't remove old torrent <b>{0}</b>"
                                .format(html.escape(old_existing_torrent['name'])))
            existing_torrent = self.clients_manager.find_torrent(torrent.info_hash)
        if not existing_torrent:
            raise Exception(u'Torrent {0} wasn\'t added'.format(filename))
        return existing_torrent['date_added']

    def execute(self, ids):
        tracker_settings = self.settings_manager.tracker_settings
        trackers = list(self.trackers_manager.trackers.items())

        execute_trackers = dict()
        tracker_topics = list()
        for name, tracker in trackers:
            topics = tracker.get_topics(ids)
            if len(topics) > 0:
                execute_trackers[name] = len(topics)
                tracker_topics.append((name, tracker, topics))

        if len(tracker_topics) == 0:
            return

        with self.notifier_manager.execute() as notifier_manager_execute:
            with self.start(execute_trackers, notifier_manager_execute) as engine_trackers:
                for name, tracker, topics in tracker_topics:
                    tracker.init(tracker_settings)
                    with engine_trackers.start(name) as engine_tracker:
                        tracker.execute(topics, engine_tracker)


class EngineExecute(object):
    def __init__(self, engine, notifier_manager_execute):
        """
        :type engine: Engine
        :type notifier_manager_execute: plugin_managers.NotifierManagerExecute
        """
        self.engine = engine
        self.notifier_manager_execute = notifier_manager_execute

    def info(self, message):
        self.engine.info(message)

    def failed(self, message, exc_type=None, exc_value=None, exc_tb=None):
        self.engine.failed(message, exc_type, exc_value, exc_tb)
        if self.notifier_manager_execute:
            try:
                self.notifier_manager_execute.notify(message)
            except:
                self.engine.failed(u"Failed notify", *sys.exc_info())

    def downloaded(self, message, torrent):
        self.engine.downloaded(message, torrent)
        if self.notifier_manager_execute:
            try:
                self.notifier_manager_execute.notify(message)
            except:
                self.engine.failed(u"Failed notify", *sys.exc_info())


class EngineTrackers(EngineExecute):
    def __init__(self, trackers_count, notifier_manager_execute, engine):
        """
        :type trackers_count: dict[str, int]
        :type notifier_manager_execute: plugin_managers.NotifierManagerExecute
        :type engine: Engine
        """
        super(EngineTrackers, self).__init__(engine, notifier_manager_execute)

        self.trackers_count = trackers_count
        self.done_topics = 0
        self.count_topics = sum(trackers_count.values())

        self.tracker_topics_count = 0

    def start(self, tracker):
        self.tracker_topics_count = self.trackers_count.pop(tracker)
        self.update_progress(0)
        engine_tracker = EngineTracker(tracker, self, self.notifier_manager_execute, self.engine)
        return engine_tracker

    def update_progress(self, progress):
        progress = _clamp(progress)
        done_progress = 100 * self.done_topics / self.count_topics
        current_progress = progress * self.tracker_topics_count / self.count_topics
        self.engine.update_progress(done_progress + current_progress)

    def __enter__(self):
        self.info(u"Begin execute")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val is not None:
            self.failed(u"Exception while execute", exc_type, exc_val, exc_tb)
        else:
            self.info(u"End execute")

        self.done_topics += self.tracker_topics_count
        self.update_progress(100)
        return True


class EngineTracker(EngineExecute):
    def __init__(self, tracker, engine_trackers, notifier_manager_execute, engine):
        """
        :type tracker: str
        :type engine_trackers: EngineTrackers
        :type notifier_manager_execute: plugin_managers.NotifierManagerExecute
        :type engine: Engine
        """
        super(EngineTracker, self).__init__(engine, notifier_manager_execute)

        self.tracker = tracker
        self.engine_trackers = engine_trackers
        self.count = 0

    def start(self, count):
        return EngineTopics(count, self, self.notifier_manager_execute, self.engine)

    def update_progress(self, progress):
        progress = _clamp(progress)
        self.engine_trackers.update_progress(progress)

    def __enter__(self):
        self.info(u"Start checking for <b>{0}</b>".format(self.tracker))
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val is not None:
            self.failed(u"Failed while checking for <b>{0}</b>".format(self.tracker),
                        exc_type, exc_val, exc_tb)
        else:
            self.info(u"End checking for <b>{0}</b>".format(self.tracker))
        return True


class EngineTopics(EngineExecute):
    def __init__(self, count, engine_tracker, notifier_manager_execute, engine):
        """
        :type count: int
        :type engine_tracker: EngineTracker
        :type notifier_manager_execute: plugin_managers.NotifierManagerExecute
        :type engine: Engine
        """
        super(EngineTopics, self).__init__(engine, notifier_manager_execute)
        self.count = count
        self.engine_tracker = engine_tracker

    def start(self, index, topic_name):
        progress = index * 100 / self.count
        self.update_progress(progress)
        return EngineTopic(topic_name, self, self.notifier_manager_execute, self.engine)

    def update_progress(self, progress):
        self.engine_tracker.update_progress(_clamp(progress))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val is not None:
            self.failed(u"Failed while checking topics", exc_type, exc_val, exc_tb)
        return True


class EngineTopic(EngineExecute):
    def __init__(self, topic_name, engine_topics, notifier_manager_execute, engine):
        """
        :type topic_name: str
        :type engine_topics: EngineTopics
        :type notifier_manager_execute: plugin_managers.NotifierManagerExecute
        :type engine: Engine
        """
        super(EngineTopic, self).__init__(engine, notifier_manager_execute)
        self.topic_name = topic_name
        self.engine_topics = engine_topics

    def start(self, count):
        return EngineDownloads(count, self, self.notifier_manager_execute, self.engine)

    def status_changed(self, old_status, new_status):
        if self.notifier_manager_execute:
            self.notifier_manager_execute.notify(u"{} status changed: {}".format(self.topic_name, new_status))

    def update_progress(self, progress):
        self.engine_topics.update_progress(_clamp(progress))

    def __enter__(self):
        self.info(u"Check for changes <b>{0}</b>".format(self.topic_name))
        self.update_progress(0)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val is not None:
            self.failed(u"Exception while execute topic", exc_type, exc_val, exc_tb)
        self.update_progress(100)
        return True


class EngineDownloads(EngineExecute):
    def __init__(self, count, engine_topic, notifier_manager_execute, engine):
        """
        :type count: int
        :type engine_topic: EngineTopic
        :type notifier_manager_execute: plugin_managers.NotifierManagerExecute
        :type engine: Engine
        """
        super(EngineDownloads, self).__init__(engine, notifier_manager_execute)
        self.count = count
        self.engine_topic = engine_topic

    def add_torrent(self, index, filename, torrent, old_hash, topic_settings):
        progress = index * 100 // self.count
        self.engine_topic.update_progress(progress)
        return self.engine.add_torrent(filename, torrent, old_hash, topic_settings)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.failed("Exception while execute", exc_type, exc_val, exc_tb)
        return True


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
    def __init__(self, log_manager, settings_manager=None):
        """
        :type log_manager: ExecuteLogManager
        :type settings_manager: settings_manager.SettingsManager | None
        """
        self._log_manager = log_manager
        self._settings_manager = settings_manager

    def started(self, start_time):
        self._log_manager.started(start_time)

    def finished(self, finish_time, exception):
        self._log_manager.finished(finish_time, exception)
        if self._settings_manager:
            self._log_manager.remove_old_entries(self._settings_manager.remove_logs_interval)

    def info(self, message):
        self._log_manager.log_entry(message, 'info')

    def failed(self, message, exc_type=None, exc_value=None, exc_tb=None):
        if exc_value is not None:
            formatted_exception = ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))
        else:
            formatted_exception = ''
        failed_message = (message + formatted_exception).replace('\n', '<br>')
        self._log_manager.log_entry(failed_message, 'failed')

    def downloaded(self, message, torrent):
        self._log_manager.log_entry(message, 'downloaded')


# noinspection PyMethodMayBeStatic
class ExecuteLogManager(object):
    _execute_id = None

    def started(self, start_time):
        if self._execute_id is not None:
            raise Exception('Execute already in progress')

        with DBSession() as db:
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
                execute.failed_message = html.escape(str(exception))

        self._execute_id = None

    def log_entry(self, message, level):
        if self._execute_id is None:
            raise Exception('Execute is not started')

        self._log_entry(message, level)

    def _log_entry(self, message, level):
        with DBSession() as db:
            execute_log = ExecuteLog(execute_id=self._execute_id, time=datetime.now(pytz.utc),
                                     message=message, level=level)
            db.add(execute_log)

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

    def __init__(self, logger, settings_manager, trackers_manager, clients_manager, notifier_manager, **kwargs):
        """
        :type logger: Logger
        :type settings_manager: settings_manager.SettingsManager
        :type trackers_manager: plugin_managers.TrackersManager
        :type clients_manager: plugin_managers.ClientsManager
        :type notifier_manager: plugin_managers.NotifierManager
        """
        interval_param = kwargs.pop('interval', None)
        last_execute_param = kwargs.pop('last_execute', None)

        super(EngineRunner, self).__init__(**kwargs)
        self.logger = logger
        self.settings_manager = settings_manager
        self.trackers_manager = trackers_manager
        self.clients_manager = clients_manager
        self.notifier_manager = notifier_manager
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
            engine = Engine(self.logger, self.settings_manager, self.trackers_manager,
                            self.clients_manager, self.notifier_manager)
            engine.execute(ids)
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

    def __init__(self, logger, settings_manager, trackers_manager, clients_manager, notifier_manager, **kwargs):
        """
        :type logger: Logger
        :type settings_manager: settings_manager.SettingsManager
        :type trackers_manager: plugin_managers.TrackersManager
        :type clients_manager: plugin_managers.ClientsManager
        :type notifier_manager: plugin_managers.NotifierManager
        """
        execute_settings = self._get_execute_settings()
        super(DBEngineRunner, self).__init__(logger,
                                             settings_manager,
                                             trackers_manager,
                                             clients_manager,
                                             notifier_manager,
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
