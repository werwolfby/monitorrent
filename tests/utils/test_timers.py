from builtins import object

from time import sleep
from tests import TestCase
from mock import MagicMock
from monitorrent.utils.timers import timer


class EngineTest(TestCase):
    def setUp(self):
        super(EngineTest, self).setUp()

    def test_timer_runs_continiously(self):
        execute_mock = MagicMock()

        cancel = timer(0.1, execute_mock)

        sleep(0.5)
        cancel()
        self.assertTrue(execute_mock.call_count > 2)

    def test_timer_passes_arguments_to_timer_func(self):
        execute_mock = MagicMock()
        cancel = timer(0.1, execute_mock, 'foo', bar='baz')

        sleep(0.2)
        cancel()

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
