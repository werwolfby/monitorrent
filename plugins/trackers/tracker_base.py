from abc import ABCMeta, abstractmethod, abstractproperty
import datetime
from db import DBSession
from utils.bittorrent import Torrent
from utils.downloader import download


class RutorLike(object):
    __metaclass__ = ABCMeta

    @abstractproperty
    def get_topic_type(self):
        return

    @abstractproperty
    def get_tracker(self):
        return

    @property
    def get_method(self):
        return None

    def parse_url(self, url):
        return self.get_tracker.parse_url(url)

    @abstractmethod
    def add_watch(self, url, display_name=None):
        return

    @abstractmethod
    def remove_watch(self, url):
        return

    @abstractmethod
    def get_watching_torrents(self):
        return

    @abstractmethod
    def execute(self, engine):
        with DBSession() as db:
            topics = db.query(self.get_topic_type).all()
            db.expunge_all()
        self.__process_torrents(topics, engine)

    @abstractmethod
    def get_request_paramerets(self, topic):
        return

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
