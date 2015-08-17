# coding=utf-8
from monitorrent.plugins.trackers.rutor import RutorOrgTracker
from unittest import TestCase
from monitorrent.tests import use_vcr


class RutorOrgTrackerTest(TestCase):
    def test_can_parse_url(self):
        tracker = RutorOrgTracker()
        self.assertTrue(tracker.can_parse_url('http://rutor.org/torrent/442959'))
        self.assertTrue(tracker.can_parse_url('http://www.rutor.org/torrent/442959'))
        self.assertTrue(tracker.can_parse_url('http://d.rutor.org/torrent/442959'))

    @use_vcr
    def test_parse_url(self):
        tracker = RutorOrgTracker()
        original_name = u'Рэй Донован / Ray Donovan [03х01-05 из 12] (2015) HDTVRip 720р | NewStudio'
        urls = ['http://rutor.org/torrent/442959',
                'http://www.rutor.org/torrent/442959']
        for url in urls:
            result = tracker.parse_url(url)
            self.assertIsNotNone(result, 'Can\'t parse url={}'.format(url))
            self.assertTrue('original_name' in result, 'Can\'t find original_name for url={}'.format(url))
            self.assertEqual(original_name, result['original_name'])

    def test_parse_url_with_full_cover(self):
        tracker = RutorOrgTracker()
        urls = ['http://www.notrutor.org/torrent/442959',
                'http://www.rutor.org/not-match-url/442959',
                'http://rutor.org/search/']
        for url in urls:
            self.assertIsNone(tracker.parse_url(url))
            self.assertIsNone(tracker.get_download_url(url))

    @use_vcr
    def test_parse_url_404(self):
        tracker = RutorOrgTracker()
        urls = ['http://www.rutor.org/torrent/123456']
        for url in urls:
            self.assertIsNone(tracker.parse_url(url))

    @use_vcr
    def test_get_hash(self):
        tracker = RutorOrgTracker()
        hash = tracker.get_hash('http://rutor.org/torrent/442959')
        self.assertIsNotNone(hash)
        self.assertEqual('C7E94D6108EA4D62877745770EF9B8F443C4E91C'.lower(), hash.lower())
        self.assertIsNone(tracker.get_hash('http://www.notrutor.org/torrent/442959'))
        with self.assertRaises(Exception):
            tracker.get_hash('http://www.rutor.org/torrent/123456')

    def test_get_download_url(self):
        tracker = RutorOrgTracker()
        urls = ['http://rutor.org/torrent/442959',
                'http://www.rutor.org/torrent/442959',
                'http://rutor.org/torrent/442959/rjej-donovan_ray-donovan-03h01-04-iz-12-2015-hdtvrip-720r-newstudio',
                'http://www.rutor.org/torrent/442959/rjej-donovan_ray-donovan-03h01-04-iz-12-2015-hdtvrip-720r-newstud']
        for url in urls:
            self.assertEqual('http://d.rutor.org/download/442959', tracker.get_download_url(url))
