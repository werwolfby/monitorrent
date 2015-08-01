from abc import ABCMeta, abstractmethod, abstractproperty
import datetime

from db import DBSession
from utils.bittorrent import Torrent
from utils.downloader import download


class TrackerBase(object):
    __metaclass__ = ABCMeta

    @abstractproperty
    def get_topic_type(self):
        pass

    @abstractproperty
    def get_tracker(self):
        pass

    @abstractproperty
    def get_credentials_type(self):
        pass

    @property
    def get_method(self):
        return None

    def parse_url(self, url):
        return self.get_tracker.parse_url(url)

    @abstractmethod
    def add_watch(self, url, display_name=None):
        pass

    @abstractmethod
    def remove_watch(self, url):
        pass

    @abstractmethod
    def get_watching_torrents(self):
        pass

    @abstractmethod
    def execute(self, engine):
        if not self._login_to_tracker(engine):
                engine.log.failed('Login to <b>tracker</b> failed')
                return
        with DBSession() as db:
            topics = db.query(self.get_topic_type).all()
            db.expunge_all()
        self.__process_torrents(topics, engine)

    @abstractmethod
    def get_request_paramerets(self, topic):
        pass

    @abstractmethod
    def verify(self):
        pass

    @abstractmethod
    def login(self, username, password):
        pass

    @staticmethod
    def _get_title(title):
        return {'original_name': title}

    def get_settings(self):
        with DBSession() as db:
            cred = db.query(self.get_credentials_type).first()
            if not cred:
                return None
            return {'username': cred.username}

    def set_settings(self, settings):
        with DBSession() as db:
            cred = db.query(self.get_credentials_type).first()
            if not cred:
                cred = self.get_credentials_type()
                db.add(cred)
            cred.username = settings['username']
            cred.password = settings['password']

    def _login_to_tracker(self, engine=None):
        with DBSession() as db:
            cred = db.query(self.get_credentials_type).first()
            if not cred:
                return False
            username = cred.username
            password = cred.password
            if not username or not password:
                return False
        if self.verify():
            if engine:
                engine.log.info('Cookies are valid')
            return True
        if engine:
            engine.log.info('Login to <b>tracker</b>')
        try:
            self.login(username, password)
        except Exception as e:
            if engine:
                engine.log.failed('Login to <b>tracker</b> failed: {0}'.format(e.message))
        return self.verify()

    def __process_torrents(self, topics, engine):
        for topic in topics:
            topic_name = topic.name
            try:
                engine.log.info(u"Check for changes <b>%s</b>" % topic_name)
                torrent_content, filename = download(self.get_tracker.get_download_url(topic.url), self.get_method,
                                                     **self.get_request_paramerets(topic))
                engine.log.downloaded(u"Torrent <b>%s</b> downloaded" % filename or topic_name, torrent_content)
                torrent = Torrent(torrent_content)
                if torrent.info_hash != topic.hash:
                    engine.log.info(u"Torrent <b>%s</b> was changed" % topic_name)
                    existing_torrent = engine.find_torrent(torrent.info_hash)
                    if existing_torrent:
                        engine.log.info(u"Torrent <b>%s</b> already added" % filename or topic_name)
                    elif engine.add_torrent(torrent_content):
                        old_existing_torrent = engine.find_torrent(topic.hash)
                        if old_existing_torrent:
                            engine.log.info(u"Updated <b>%s</b>" % filename or topic_name)
                        else:
                            engine.log.info(u"Add new <b>%s</b>" % filename or topic_name)
                        if old_existing_torrent:
                            if engine.remove_torrent(topic.hash):
                                engine.log.info(u"Remove old torrent <b>%s</b>" %
                                                old_existing_torrent['name'])
                            else:
                                engine.log.failed(u"Can't remove old torrent <b>%s</b>" %
                                                  old_existing_torrent['name'])
                        existing_torrent = engine.find_torrent(torrent.info_hash)
                    if existing_torrent:
                        last_update = existing_torrent['date_added']
                    else:
                        last_update = datetime.datetime.now()
                    with DBSession() as db:
                        db.add(topic)
                        topic.hash = torrent.info_hash
                        topic.last_update = last_update
                        db.commit()
                else:
                    engine.log.info(u"Torrent <b>%s</b> not changed" % topic_name)
            except Exception as e:
                engine.log.failed(u"Failed update <b>%s</b>.\nReason: %s" % (topic_name, e.message))

    @staticmethod
    def _get_torrent_info(topic):
        return {
            "id": topic.id,
            "name": topic.name,
            "url": topic.url,
            "info": None,
            "last_update": topic.last_update.isoformat() if topic.last_update else None
        }
