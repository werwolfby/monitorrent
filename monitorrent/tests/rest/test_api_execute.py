import json
import falcon
from datetime import datetime
from Queue import Queue
from unittest import TestCase
from mock import MagicMock, Mock
import pytz
from monitorrent.engine import Logger
from monitorrent.tests import RestTestBase
from monitorrent.rest.execute import ExecuteLogCurrent, EngineRunnerLoggerWrapper, ExecuteCall


class ExecuteCallTest(RestTestBase):
    def test_execute(self):
        engine_runner = Mock
        engine_runner.execute = MagicMock()
        # noinspection PyTypeChecker
        execute_call = ExecuteCall(engine_runner)

        self.api.add_route(self.test_route, execute_call)

        self.simulate_request(self.test_route, method="POST")

        self.assertEqual(self.srmock.status, falcon.HTTP_OK)

        engine_runner.execute.assert_called_once_with()


class EngineRunnerLoggerTest(TestCase):
    def test_single_queue_items(self):
        logger = EngineRunnerLoggerWrapper(Logger())
        queue = Queue()
        logger.attach(queue)

        logger.started()
        logger.info('Info')
        logger.downloaded('Downloaded', '1234')
        logger.failed('Failed')
        logger.finished(datetime.now(pytz.utc), None)

        logger.detach(queue)

        events = self._read_from_queue(queue)

        self.assertEqual(5, len(events))

        self.assertEqual(events[0]['event'], 'started')
        self.assertEqual(events[1]['event'], 'log')
        self.assertEqual(events[2]['event'], 'log')
        self.assertEqual(events[3]['event'], 'log')
        self.assertEqual(events[4]['event'], 'finished')

    def test_attach_in_middle(self):
        logger = EngineRunnerLoggerWrapper(Logger())
        queue1 = Queue()
        queue2 = Queue()
        logger.attach(queue1)

        logger.started()
        logger.info('Info')
        logger.downloaded('Downloaded', '1234')

        logger.attach(queue2)

        logger.failed('Failed')
        logger.finished(datetime.now(pytz.utc), None)

        logger.detach(queue1)
        logger.detach(queue2)

        def assert_events(events):
            self.assertEqual(5, len(events))

            self.assertEqual(events[0]['event'], 'started')
            self.assertEqual(events[1]['event'], 'log')
            self.assertEqual(events[2]['event'], 'log')
            self.assertEqual(events[3]['event'], 'log')
            self.assertEqual(events[4]['event'], 'finished')

        assert_events(self._read_from_queue(queue1))
        assert_events(self._read_from_queue(queue2))


    @staticmethod
    def _read_from_queue(queue):
        events = list()
        while True:
            data = queue.get(timeout=1)
            if data is not None:
                events.append(data)
            else:
                break
        return events
