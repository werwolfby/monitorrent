import json
import falcon
from datetime import datetime
from Queue import Queue
from unittest import TestCase
from mock import MagicMock, Mock
from monitorrent.tests import RestTestBase
from monitorrent.rest.execute import ExecuteLogCurrent, EngineRunnerLogger, ExecuteCall


class ExecuteLogCurrentTest(RestTestBase):
    def test_simple_log(self):
        attach_mock, detach_mock, logger = self._create_logger()
        execute_log = ExecuteLogCurrent(logger)

        self.api.add_route(self.test_route, execute_log)

        body = self.simulate_request(self.test_route)
        resp = next(body)
        queue = attach_mock.call_args_list[0][0][0]

        e1 = {'test': '1'}
        e2 = {'test': '2'}
        queue.put(e1)
        queue.put(e2)
        queue.put(None)

        for r in body:
            resp += r

        resp_parsed = json.loads(resp)

        self.assertEqual(2, len(resp_parsed))
        self.assertEqual(resp_parsed, [e1, e2])

        self.assertTrue(attach_mock.called)
        self.assertEqual(attach_mock.call_count, 1)

        self.assertTrue(detach_mock.called)
        self.assertEqual(detach_mock.call_count, 1)

    def test_break(self):
        attach_mock, detach_mock, logger = self._create_logger()
        execute_log = ExecuteLogCurrent(logger, timeout=1)

        self.api.add_route(self.test_route, execute_log)

        body = self.simulate_request(self.test_route)
        resp = next(body)

        for r in body:
            resp += r

        resp_parsed = json.loads(resp)

        self.assertEqual(0, len(resp_parsed))
        self.assertEqual(resp_parsed, [])

        self.assertTrue(attach_mock.called)
        self.assertEqual(attach_mock.call_count, 1)

        self.assertTrue(detach_mock.called)
        self.assertEqual(detach_mock.call_count, 1)

    def test_exit(self):
        attach_mock, detach_mock, logger = self._create_logger()
        execute_log = ExecuteLogCurrent(logger, timeout=1)

        self.api.add_route(self.test_route, execute_log)

        body = self.simulate_request(self.test_route)
        next(body)
        body.close()

        self.assertTrue(attach_mock.called)
        self.assertEqual(attach_mock.call_count, 1)

        self.assertTrue(detach_mock.called)
        self.assertEqual(detach_mock.call_count, 1)

    def _create_logger(self):
        logger = EngineRunnerLogger()
        attach_mock = MagicMock()
        detach_mock = MagicMock()
        logger.attach = attach_mock
        logger.detach = detach_mock
        return attach_mock, detach_mock, logger


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
        logger = EngineRunnerLogger()
        queue = Queue()
        logger.attach(queue)

        logger.started()
        logger.info('Info')
        logger.downloaded('Downloaded', '1234')
        logger.failed('Failed')
        logger.finished(datetime.now(), None)

        logger.detach(queue)

        events = self._read_from_queue(queue)

        self.assertEqual(5, len(events))

        self.assertEqual(events[0]['event'], 'started')
        self.assertEqual(events[1]['event'], 'log')
        self.assertEqual(events[2]['event'], 'log')
        self.assertEqual(events[3]['event'], 'log')
        self.assertEqual(events[4]['event'], 'finished')

    def test_attach_in_middle(self):
        logger = EngineRunnerLogger()
        queue1 = Queue()
        queue2 = Queue()
        logger.attach(queue1)

        logger.started()
        logger.info('Info')
        logger.downloaded('Downloaded', '1234')

        logger.attach(queue2)

        logger.failed('Failed')
        logger.finished(datetime.now(), None)

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
