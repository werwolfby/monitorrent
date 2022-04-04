# coding=utf-8
from monitorrent.plugins.trackers import TrackerSettings
from monitorrent.plugins.trackers.rutor import RutorOrgTracker
from unittest import TestCase
from tests import use_vcr


class RutorOrgTrackerTest(TestCase):
    def setUp(self):
        super(RutorOrgTrackerTest, self).setUp()
        self.tracker_settings = TrackerSettings(10, 30000, None)

    def test_can_parse_url(self):
        tracker = RutorOrgTracker()
        tracker.tracker_settings = self.tracker_settings
        self.assertTrue(tracker.can_parse_url('http://rutor.info/torrent/442959'))
        self.assertTrue(tracker.can_parse_url('http://www.rutor.info/torrent/442959'))
        self.assertTrue(tracker.can_parse_url('http://d.rutor.info/torrent/442959'))
        self.assertTrue(tracker.can_parse_url('http://rutor.is/torrent/442959'))
        self.assertTrue(tracker.can_parse_url('http://www.rutor.is/torrent/442959'))
        self.assertTrue(tracker.can_parse_url('http://d.rutor.is/torrent/442959'))
        self.assertFalse(tracker.can_parse_url('http://notrutor.info/torrent/442959'))
        self.assertFalse(tracker.can_parse_url('http://notrutor.is/torrent/442959'))
        self.assertFalse(tracker.can_parse_url('http://subdomain.notrutor.is/torrent/442959'))

    @use_vcr
    def test_parse_url(self):
        tracker = RutorOrgTracker()
        tracker.tracker_settings = self.tracker_settings
        original_name = u'Время приключений с Финном и Джейком / Adventure Time with Finn & Jake ' + \
                        u'[S01-06] (2010-2015) WEB-DL 720p | Cartoon Network, Зебуро'
        urls = ['http://rutor.info/torrent/466037',
                'http://www.rutor.info/torrent/466037',
                'http://rutor.is/torrent/466037',
                'http://www.rutor.is/torrent/466037']
        for url in urls:
            result = tracker.parse_url(url)
            self.assertIsNotNone(result, 'Can\'t parse url={}'.format(url))
            self.assertTrue('original_name' in result, 'Can\'t find original_name for url={}'.format(url))
            self.assertEqual(original_name, result['original_name'])

    def test_parse_url_with_full_cover(self):
        tracker = RutorOrgTracker()
        tracker.tracker_settings = self.tracker_settings
        urls = ['http://www.notrutor.info/torrent/442959',
                'http://www.rutor.info/not-match-url/442959',
                'http://rutor.info/search/']
        for url in urls:
            self.assertIsNone(tracker.parse_url(url))
            self.assertIsNone(tracker.get_download_url(url))

    @use_vcr
    def test_parse_url_404(self):
        tracker = RutorOrgTracker()
        tracker.tracker_settings = self.tracker_settings
        urls = ['http://www.rutor.info/torrent/123456']
        for url in urls:
            self.assertIsNone(tracker.parse_url(url))

    def test_get_download_url(self):
        tracker = RutorOrgTracker()
        tracker.tracker_settings = self.tracker_settings
        urls = ['http://rutor.info/torrent/442959',
                'http://www.rutor.info/torrent/442959',
                'http://rutor.info/torrent/442959/rjej-donovan_ray-donovan-03h01-04-iz-12-2015-hdtvrip-720r-newstudio',
                'http://www.rutor.info/torrent/442959/rjej-donovan_ray-donovan-03h01-04-iz-12-2015-hdtvrip-720r-newstud']
        for url in urls:
            self.assertEqual('http://rutor.info/download/442959', tracker.get_download_url(url))
