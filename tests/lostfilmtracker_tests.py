# coding=utf-8
from plugins.lostfilm import LostFilmTVTracker, LostFilmTVLoginFailedException
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
