import requests
from ddt import ddt, data
from monitorrent.tests import TestCase, use_vcr
from monitorrent.utils.downloader import download


@ddt
class DownloaderTest(TestCase):
    @data(False, True)
    @use_vcr
    def test_string_downloader(self, prepared=False):
        url = 'http://google.com'
        if prepared:
            url = self.prepare_reques(url)
        response, filename = download(url)

        self.assertEqual(9766, len(response.content))
        self.assertIsNone(filename)

    @data(False, True)
    @use_vcr
    def test_file_downloader(self, prepared=False):
        url = 'http://d.rutor.org/download/442959'
        if prepared:
            url = self.prepare_reques(url)
        response, filename = download(url)

        self.assertEqual(32814, len(response.content))
        self.assertEqual(filename, '[rutor.org]Ray.Donovan_S03_720p.NewStudio.torrent')

    def prepare_reques(self, url):
        request = requests.Request('GET', url)
        return request.prepare()
