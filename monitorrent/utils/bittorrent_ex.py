"""
Add raw_content to original flexget bittorrent class
"""
import six
from monitorrent.utils.bittorrent import Torrent as FlexgetTorrent, TORRENT_RE


def is_torrent_content(data):
    """ Check whether a file looks like a metafile by peeking into its content.

        Note that this doesn't ensure that the file is a complete and valid torrent,
        it just allows fast filtering of candidate files.

        @param data: content of torrent file.
        @return: True if there is a high probability this is a metafile.
    """
    if isinstance(data, six.text_type):
        data = data.encode('utf-8')

    return bool(TORRENT_RE.match(data))


class Torrent(FlexgetTorrent):
    def __init__(self, content):
        content = content.strip()
        super(Torrent, self).__init__(content)
        self.raw_content = content
