"""
Add raw_content to original flexget bittorrent class
"""
from monitorrent.utils.bittorrent import Torrent as FlexgetTorrent


class Torrent(FlexgetTorrent):
    def __init__(self, content):
        content = content.strip()
        super(Torrent, self).__init__(content)
        self.raw_content = content
