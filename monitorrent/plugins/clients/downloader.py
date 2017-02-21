import os
from datetime import datetime
from builtins import object
from pytz import reference, utc
from sqlalchemy import Column, Integer, String
from monitorrent.db import Base, DBSession
from monitorrent.plugin_managers import register_plugin
from monitorrent.plugins.clients import DownloadStatus
from monitorrent.utils.bittorrent_ex import Torrent
import base64


class DownloaderSettings(Base):
    __tablename__ = "downloader_settings"

    id = Column(Integer, primary_key=True)
    path = Column(String, nullable=False)


class DownloaderPlugin(object):
    name = "downloader"
    form = [{
        'type': 'row',
        'content': [{
            'type': 'text',
            'label': 'Path',
            'model': 'path',
            'flex': 100
        }]
    }]
    SUPPORTED_FIELDS = []

    def get_settings(self):
        with DBSession() as db:
            cred = db.query(DownloaderSettings).first()
            if not cred:
                return None
            return {'path': cred.path}

    def set_settings(self, settings):
        with DBSession() as db:
            cred = db.query(DownloaderSettings).first()
            if not cred:
                cred = DownloaderSettings()
                db.add(cred)
            cred.path = settings['path']

    def check_connection(self):
        with DBSession() as db:
            cred = db.query(DownloaderSettings).first()
            if not cred:
                return False
            try:
                if not os.path.exists(cred.path):
                    os.makedirs(cred.path)
                if not os.access(cred.path, os.W_OK):
                    return False
                return cred.path
            except OSError:
                return False

    def find_torrent(self, torrent_hash):
        path = self.check_connection()
        if not path:
            return False
        files = os.listdir(path)
        for torrent_file in files:
            file_path = os.path.join(path, torrent_file)
            if torrent_file.endswith(".torrent") and os.path.isfile(file_path):
                try:
                    try:
                        torrent = Torrent.from_file(file_path)
                    except:
                        continue
                    if torrent.info_hash == torrent_hash:
                        date_added = datetime.fromtimestamp(os.path.getctime(file_path))\
                            .replace(tzinfo=reference.LocalTimezone()).astimezone(utc)
                        return {"name": torrent_file, "date_added": date_added}
                except OSError:
                    continue
        return False

    def add_torrent(self, torrent_content, torrent_settings):
        path = self.check_connection()
        if not path:
            return False
        try:
            try:
                torrent = Torrent(torrent_content)
            except Exception as e:
                return False
            filename = torrent.info_hash + ".torrent"
            with open(os.path.join(path, filename), "wb") as f:
                f.write(torrent.raw_content)
            return True
        except OSError:
            return False

    def remove_torrent(self, torrent_hash):
        path = self.check_connection()
        if not path:
            return False
        try:
            torrent = self.find_torrent(torrent_hash)
            if not torrent:
                return False
            os.remove(os.path.join(path, torrent["name"]))
            return True
        except OSError:
            return False

    def get_download_status(self, torrent_hash):
        return DownloadStatus(0, 0, 0, 0)

register_plugin('client', DownloaderPlugin.name, DownloaderPlugin())
