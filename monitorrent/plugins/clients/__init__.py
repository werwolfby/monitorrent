from enum import Enum

from monitorrent.plugins.trackers import Topic


class TorrentDownloadStatus(Enum):
    Queued = 1,
    Preparing = 2,
    Checking = 3,
    Downloading = 5,
    Verifying = 6,
    Finished = 7,
    Seeding = 8,
    Paused = 9,
    Error = 10,
    Unknown = 20


class DownloadStatus(dict):
    def __init__(self, downloaded_bytes, total_bytes, download_speed, upload_speed, torrent_status, progress, ratio):
        """
        :type downloaded_bytes: int
        :type total_bytes: int
        :type download_speed: int
        :type upload_speed: int
        :type torrent_status: TorrentDownloadStatus
        :type progress: float
        :type ratio: float
        """

        super(DownloadStatus, self).__init__()
        self.downloaded_bytes = downloaded_bytes
        self.total_bytes = total_bytes
        self.download_speed = download_speed
        self.upload_speed = upload_speed
        self.torrent_status = torrent_status
        self.progress = progress
        self.ratio = ratio


class TopicSettings(object):
    download_dir = None

    def __init__(self, download_dir):
        """
        :type download_dir: str | None
        """
        super(TopicSettings, self).__init__()
        self.download_dir = download_dir

    @staticmethod
    def from_topic(topic):
        """
        :type topic: Topic
        """
        return TopicSettings(topic.download_dir)
