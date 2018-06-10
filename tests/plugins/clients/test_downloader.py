import os
import sys
import shutil
from datetime import datetime
from mock import patch, mock_open, MagicMock, Mock
from tests import DbTestCase, ReadContentMixin, tests_dir
from monitorrent.plugins.clients.downloader import DownloaderPlugin
from monitorrent.utils.bittorrent_ex import Torrent
from pytz import reference, utc


class DownloaderTest(ReadContentMixin, DbTestCase):
    def setUp(self):
        super(DownloaderTest, self).setUp()
        dirpath = os.path.dirname(os.path.realpath(__file__))
        self.downloader_dir = os.path.join(dirpath, "torrents")
        self._remove_dowloader_dir()

    def tearDown(self):
        self._remove_dowloader_dir()

    def test_settings(self):
        plugin = DownloaderPlugin()
        settings = {'path': self.downloader_dir}
        self.assertIsNone(plugin.get_settings())
        plugin.set_settings(settings)
        readed_settings = plugin.get_settings()

        self.assertEqual({'path': self.downloader_dir}, readed_settings)

    def test_check_connection_successful(self):
        plugin = DownloaderPlugin()
        settings = {'path': self.downloader_dir}
        plugin.set_settings(settings)

        self.assertEqual(self.downloader_dir, plugin.check_connection())

    def test_check_connection_failed(self):
        plugin = DownloaderPlugin()
        settings = {'path': ('C:/torrents' if sys.platform == 'win32' else '/dev/somedevice')}
        plugin.set_settings(settings)

        with patch("os.access") as os_access:
            os_access.return_value = False
            self.assertFalse(plugin.check_connection())

    def test_check_connection_failed_access(self):
        plugin = DownloaderPlugin()
        settings = {'path': self.downloader_dir}
        plugin.set_settings(settings)

        with patch('monitorrent.plugins.clients.downloader.os.access') as access:
            access.return_value = False
            self.assertFalse(plugin.check_connection())

    def test_find_torrent(self):
        torrent_filename = 'Hell.On.Wheels.S05E02.720p.WEB.rus.LostFilm.TV.mp4.torrent'
        torrent_filepath = self.get_httpretty_filename(torrent_filename)
        torrent = Torrent.from_file(torrent_filepath)

        plugin = DownloaderPlugin()
        settings = {'path': self.downloader_dir}
        self.assertFalse(plugin.find_torrent(torrent.info_hash))
        plugin.set_settings(settings)

        self.assertFalse(plugin.find_torrent(torrent.info_hash))

        downloaded_filepath = os.path.join(self.downloader_dir, torrent_filename)
        if not os.path.exists(self.downloader_dir):
            os.makedirs(self.downloader_dir)
        shutil.copy(torrent_filepath, downloaded_filepath)

        find_torrent = plugin.find_torrent(torrent.info_hash)
        self.assertNotEqual(False, find_torrent)
        date_added = datetime.fromtimestamp(os.path.getctime(downloaded_filepath))\
            .replace(tzinfo=reference.LocalTimezone()).astimezone(utc)
        expected = {'name': torrent_filename, 'date_added': date_added}
        self.assertEqual(expected, find_torrent)

    def test_find_torrent_unexist_hash_failed(self):
        plugin = DownloaderPlugin()
        settings = {'path': self.downloader_dir}
        plugin.set_settings(settings)

        self.assertFalse(plugin.find_torrent("TORRENT_HASH"))

    def test_find_torrent_wrong_file_extension_failed(self):
        plugin = DownloaderPlugin()
        settings = {'path': self.downloader_dir}
        plugin.set_settings(settings)

        os.makedirs(self.downloader_dir)
        with open(os.path.join(self.downloader_dir, "1.txt"), "w") as f:
            f.write("Not A Torrent File")

        self.assertFalse(plugin.find_torrent("TORRENT_HASH"))

    def test_find_torrent_wrong_file_format_failed(self):
        plugin = DownloaderPlugin()
        settings = {'path': self.downloader_dir}
        plugin.set_settings(settings)

        os.makedirs(self.downloader_dir)
        with open(os.path.join(self.downloader_dir, "1.torrent"), "w") as f:
            f.write("Fake Torrent File")

        self.assertFalse(plugin.find_torrent("TORRENT_HASH"))

    def test_find_torrent_failed_os_error(self):
        torrent_filename = 'Hell.On.Wheels.S05E02.720p.WEB.rus.LostFilm.TV.mp4.torrent'
        torrent_filepath = self.get_httpretty_filename(torrent_filename)
        torrent = Torrent.from_file(torrent_filepath)

        plugin = DownloaderPlugin()
        settings = {'path': self.downloader_dir}
        plugin.set_settings(settings)

        downloaded_filepath = os.path.join(self.downloader_dir, torrent_filename)
        if not os.path.exists(self.downloader_dir):
            os.makedirs(self.downloader_dir)
        shutil.copy(torrent_filepath, downloaded_filepath)

        with patch('monitorrent.plugins.clients.downloader.os.path.getctime') as access:
            access.side_effect = OSError
            self.assertFalse(plugin.find_torrent(torrent.info_hash))

    def test_add_torrent_success(self):
        torrent = self.read_httpretty_content('Hell.On.Wheels.S05E02.720p.WEB.rus.LostFilm.TV.mp4.torrent', 'rb')

        plugin = DownloaderPlugin()
        settings = {'path': self.downloader_dir}
        self.assertFalse(plugin.add_torrent(torrent, None))
        plugin.set_settings(settings)

        self.assertTrue(plugin.add_torrent(torrent, None))
        created_file = os.path.join(self.downloader_dir, "A7BF281BE37BAF50E5725584DAF93AEFB3DD484A.torrent")
        self.assertTrue(os.path.exists(created_file))

    def test_add_torrent_failed_1(self):
        plugin = DownloaderPlugin()
        settings = {'path': self.downloader_dir}
        plugin.set_settings(settings)

        self.assertFalse(plugin.add_torrent("FAKE TORRENT", None))

    def test_add_torrent_failed_2(self):
        torrent = self.read_httpretty_content('Hell.On.Wheels.S05E02.720p.WEB.rus.LostFilm.TV.mp4.torrent', 'rb')

        plugin = DownloaderPlugin()
        settings = {'path': self.downloader_dir}
        plugin.set_settings(settings)

        open_mock = MagicMock(side_effect=OSError)
        with patch("monitorrent.plugins.clients.downloader.open", open_mock):
            self.assertFalse(plugin.add_torrent(torrent, None))

    def _remove_dowloader_dir(self):
        if os.path.exists(self.downloader_dir):
            shutil.rmtree(self.downloader_dir)

    def test_remove_torrent(self):
        torrent_filename = 'Hell.On.Wheels.S05E02.720p.WEB.rus.LostFilm.TV.mp4.torrent'
        torrent_filepath = self.get_httpretty_filename(torrent_filename)
        torrent = Torrent.from_file(torrent_filepath)

        plugin = DownloaderPlugin()
        self.assertFalse(plugin.remove_torrent(torrent.info_hash))
        settings = {'path': self.downloader_dir}
        plugin.set_settings(settings)

        self.assertFalse(plugin.remove_torrent(torrent.info_hash))

        downloaded_filepath = os.path.join(self.downloader_dir, torrent_filename)
        if not os.path.exists(self.downloader_dir):
            os.makedirs(self.downloader_dir)
        shutil.copy(torrent_filepath, downloaded_filepath)

        self.assertFalse(plugin.remove_torrent("RANDOM_HASH"))

        self.assertTrue(plugin.remove_torrent(torrent.info_hash))
        self.assertFalse(os.path.exists(downloaded_filepath))

    def test_remove_torrent_failed(self):
        torrent_filename = 'Hell.On.Wheels.S05E02.720p.WEB.rus.LostFilm.TV.mp4.torrent'
        torrent_filepath = self.get_httpretty_filename(torrent_filename)
        torrent = Torrent.from_file(torrent_filepath)

        plugin = DownloaderPlugin()
        self.assertFalse(plugin.remove_torrent(torrent.info_hash))
        settings = {'path': self.downloader_dir}
        plugin.set_settings(settings)

        downloaded_filepath = os.path.join(self.downloader_dir, torrent_filename)
        if not os.path.exists(self.downloader_dir):
            os.makedirs(self.downloader_dir)
        shutil.copy(torrent_filepath, downloaded_filepath)

        with patch('monitorrent.plugins.clients.downloader.os.remove') as remove:
            remove.side_effect = OSError
            self.assertFalse(plugin.remove_torrent(torrent.info_hash))
        self.assertTrue(os.path.exists(downloaded_filepath))
