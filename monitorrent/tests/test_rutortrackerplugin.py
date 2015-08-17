# coding=utf-8
from monitorrent.db import init_db_engine, create_db, close_db
from monitorrent.plugins.trackers.rutor import RutorOrgPlugin, RutorOrgTopic
from monitorrent.tests import use_vcr, DbTestCase
import datetime


class RutorTrackerPluginTest(DbTestCase):
    def test_can_parse_url(self):
        tracker = RutorOrgPlugin()
        self.assertTrue(tracker.can_parse_url('http://rutor.org/torrent/442959'))
        self.assertTrue(tracker.can_parse_url('http://www.rutor.org/torrent/442959'))
        self.assertTrue(tracker.can_parse_url('http://d.rutor.org/torrent/442959'))

    @use_vcr
    def test_parse_url(self):
        tracker = RutorOrgPlugin()
        original_name = u'Рэй Донован / Ray Donovan [03х01-05 из 12] (2015) HDTVRip 720р | NewStudio'
        urls = ['http://rutor.org/torrent/442959',
                'http://www.rutor.org/torrent/442959']
        for url in urls:
            result = tracker.parse_url(url)
            self.assertIsNotNone(result, 'Can\'t parse url={}'.format(url))
            self.assertTrue('original_name' in result, 'Can\'t find original_name for url={}'.format(url))
            self.assertEqual(original_name, result['original_name'])

    def test_parse_url_with_full_cover(self):
        tracker = RutorOrgPlugin()
        urls = ['http://www.notrutor.org/torrent/442959',
                'http://www.rutor.org/not-match-url/442959',
                'http://rutor.org/search/']
        for url in urls:
            self.assertIsNone(tracker.parse_url(url))

    def test_prepare_request(self):
        tracker = RutorOrgPlugin()
        urls = ['http://rutor.org/torrent/442959',
                'http://www.rutor.org/torrent/442959',
                'http://rutor.org/torrent/442959/rjej-donovan_ray-donovan-03h01-04-iz-12-2015-hdtvrip-720r-newstudio',
                'http://www.rutor.org/torrent/442959/rjej-donovan_ray-donovan-03h01-04-iz-12-2015-hdtvrip-720r-newstud']
        for url in urls:
            topic = RutorOrgTopic(url=url)
            self.assertEqual('http://d.rutor.org/download/442959', tracker._prepare_request(topic))
