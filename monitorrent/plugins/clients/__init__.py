from monitorrent.plugins.trackers import Topic


class DownloadStatus(dict):
    def __init__(self, downloaded_bytes, total_bytes, download_speed, upload_speed):
        self.downloaded_bytes = downloaded_bytes
        self.total_bytes = total_bytes
        self.download_speed = download_speed
        self.upload_speed = upload_speed

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
