from time import sleep
from unittest import TestCase
from mock import Mock, patch
from ddt import ddt, data
from monitorrent.new_version_checker import NewVersionChecker
from monitorrent.tests import use_vcr


@ddt
class NewVersionCheckerTest(TestCase):
    @use_vcr()
    def test_get_latest_public_release(self):
        checker = NewVersionChecker(False)

        self.assertEqual('1.0.2', checker.get_latest_release())

    @use_vcr()
    def test_get_latest_prerelease_release(self):
        checker = NewVersionChecker(True)

        self.assertEqual('1.1.0-rc.1.1', checker.get_latest_release())

    @use_vcr()
    @data('0.0.3-alpha', '1.0.0', '1.0.1')
    def test_new_public_version_url(self, version):
        checker = NewVersionChecker(False)

        with patch('monitorrent.new_version_checker.monitorrent', create=True) as version_mock:
            version_mock.__version__ = version

            checker.execute()

            self.assertEqual('https://github.com/werwolfby/monitorrent/releases/tag/1.0.2', checker.new_version_url)

    def test_timer_calls(self):
        checker = NewVersionChecker(False)

        execute_mock = Mock(return_value=True)
        checker.execute = execute_mock

        checker.start(0.1)
        sleep(0.3)
        checker.stop()

        self.assertGreaterEqual(execute_mock.call_count, 2)
        self.assertLess(execute_mock.call_count, 4)

        sleep(0.3)

        self.assertLess(execute_mock.call_count, 4)

    def test_timer_stop_dont_call_execute(self):
        checker = NewVersionChecker(False)

        execute_mock = Mock(return_value=True)
        checker.execute = execute_mock

        checker.start(1)
        checker.stop()

        execute_mock.assert_not_called()

        self.assertLess(execute_mock.call_count, 4)

    def test_start_twice_should_raise(self):
        checker = NewVersionChecker(False)

        execute_mock = Mock(return_value=True)
        checker.execute = execute_mock

        checker.start(10)
        with self.assertRaises(Exception):
            checker.start(10)
        checker.stop()

        execute_mock.assert_not_called()
