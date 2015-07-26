# coding=utf-8
from plugins.trackers.lostfilm import LostFilmTVTracker, LostFilmTVLoginFailedException
from unittest import TestCase
from tests import test_vcr
import vcr

# for real test set real values
REAL_LOGIN = 'fake_login'
REAL_PASSWORD = 'fake_password'
REAL_UID = '806527' # this are 3 random strings
REAL_PASS = 'bfea24c26ddaa76f4da7852e16e0327d'
REAL_USESS = 'ce32569594e058c44d162c0df062c751'

lostfilm_vcr = vcr.VCR(
    cassette_library_dir=test_vcr.cassette_library_dir,
    record_mode=test_vcr.record_mode
)

use_vcr = lostfilm_vcr.use_cassette


class LostFilmTrackerTest(TestCase):
    @use_vcr(filter_post_data_parameters=['login', 'password'])
    def test_login(self):
        tracker = LostFilmTVTracker()
        tracker.login(REAL_LOGIN, REAL_PASSWORD)
        self.assertTrue(tracker.c_uid == REAL_UID)
        self.assertTrue(tracker.c_pass == REAL_PASS)
        self.assertTrue(tracker.c_usess == REAL_USESS)

    @use_vcr()
    def test_fail_login(self):
        tracker = LostFilmTVTracker()
        with self.assertRaises(LostFilmTVLoginFailedException) as cm:
            tracker.login(REAL_LOGIN, "FAKE_PASSWORD")
        self.assertTrue(cm.exception.code, 6)
        self.assertTrue(cm.exception.text, 'incorrect login/password')
        self.assertTrue(cm.exception.message, u'Не удалось войти. Возможно не правильный логин/пароль')

    @use_vcr()
    def test_verify(self):
        tracker = LostFilmTVTracker(REAL_UID, REAL_PASS, REAL_USESS)
        self.assertTrue(tracker.verify())

    @use_vcr()
    def test_verify_fail(self):
        tracker = LostFilmTVTracker("457686", '1'*32, '2'*32)
        self.assertFalse(tracker.verify())

    def test_parse_correct_title(self):
        title = LostFilmTVTracker._parse_title(u'Род человеческий (Extant)')
        self.assertEqual(u'Род человеческий', title['name'])
        self.assertEqual(u'Extant', title['original_name'])

    @use_vcr()
    def test_parse_correct_url(self):
        tracker = LostFilmTVTracker("457686", '1'*32, '2'*32)
        title = tracker.parse_url('http://www.lostfilm.tv/browse.php?cat=236')
        self.assertEqual(u'12 обезьян', title['name'])
        self.assertEqual(u'12 Monkeys', title['original_name'])

    def test_parse_corrent_rss_title0(self):
        t1 = u'Мистер Робот (Mr. Robot). уя3вим0сти.wmv (3xpl0its.wmv) [MP4]. (S01E05)'
        parsed = LostFilmTVTracker.parse_rss_title(t1)
        self.assertEqual(u'Мистер Робот', parsed['name'])
        self.assertEqual(u'Mr. Robot', parsed['original_name'])
        self.assertEqual(u'уя3вим0сти.wmv', parsed['title'])
        self.assertEqual(u'3xpl0its.wmv', parsed['original_title'])
        self.assertEqual(u'720p', parsed['quality'])
        self.assertEqual(u'S01E05', parsed['episode_info'])
        self.assertEqual(1, parsed['season'])
        self.assertEqual(5, parsed['episode'])

    def test_parse_corrent_rss_title1(self):
        t1 = u'Мистер Робот (Mr. Robot). уя3вим0сти.wmv (3xpl0its.wmv). (S01E05)'
        parsed = LostFilmTVTracker.parse_rss_title(t1)
        self.assertEqual(u'Мистер Робот', parsed['name'])
        self.assertEqual(u'Mr. Robot', parsed['original_name'])
        self.assertEqual(u'уя3вим0сти.wmv', parsed['title'])
        self.assertEqual(u'3xpl0its.wmv', parsed['original_title'])
        self.assertEqual(u'SD', parsed['quality'])
        self.assertEqual(u'S01E05', parsed['episode_info'])
        self.assertEqual(1, parsed['season'])
        self.assertEqual(5, parsed['episode'])

    def test_parse_special_rss_title(self):
        t1 = u'Под куполом (Under the Dome). Идите дальше/А я останусь (Move On/But I\'m Not) [1080p]. (S03E01E02)'
        parsed = LostFilmTVTracker.parse_rss_title(t1)
        self.assertEqual(u'Под куполом', parsed['name'])
        self.assertEqual(u'Under the Dome', parsed['original_name'])
        self.assertEqual(u'Идите дальше/А я останусь', parsed['title'])
        self.assertEqual(u'Move On/But I\'m Not', parsed['original_title'])
        self.assertEqual(u'1080p', parsed['quality'])
        self.assertEqual(u'S03E01E02', parsed['episode_info'])
        self.assertEqual(3, parsed['season'])
        self.assertEqual(2, parsed['episode'])
