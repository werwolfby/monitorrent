from time import sleep
from tests import TestCase
from mock import MagicMock, patch
from monitorrent.utils.timers import timer


class TimersTest(TestCase):
    def setUp(self):
        super(TimersTest, self).setUp()

    def test_timer_runs_continiously(self):
        execute_mock = MagicMock()

        cancel = timer(0.1, execute_mock)

        sleep(0.5)
        cancel()
        self.assertTrue(execute_mock.call_count > 2)

    def test_timer_passes_arguments_to_timer_func(self):
        execute_mock = MagicMock()
        cancel = timer(0.1, execute_mock, 'foo', bar='baz')

        sleep(0.15)
        cancel()

        self.assertEqual(execute_mock.call_count, 1)
        execute_mock.assert_called_once_with('foo', bar='baz')

    def test_timer_dont_run_after_cancellation(self):
        execute_mock = MagicMock()
        cancel = timer(0.1, execute_mock)

        sleep(0.5)
        cancel()

        self.assertTrue(execute_mock.call_count > 2)
        expected_call_count = execute_mock.call_count

        sleep(0.5)
        self.assertEqual(execute_mock.call_count, expected_call_count)

    def test_timer_starts_daemon_thread(self):
        execute_mock = MagicMock()
        timer_thread = MagicMock()

        with patch('threading.Thread') as thread_mock:
            thread_mock.return_value = timer_thread

            cancel = timer(0.1, execute_mock)

            assert hasattr(timer_thread, "daemon")
            assert timer_thread.daemon is True

            cancel()
