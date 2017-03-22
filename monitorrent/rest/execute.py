from builtins import object
import time
import falcon
import structlog

from monitorrent.plugins.status import Status
from monitorrent.engine import EngineRunner, ExecuteLogManager

log = structlog.get_logger()


# noinspection PyUnusedLocal
class ExecuteLogCurrent(object):
    def __init__(self, log_manager):
        """
        :type log_manager: ExecuteLogManager
        """
        self.log_manager = log_manager

    def on_get(self, req, resp):
        try:
            after = req.get_param_as_int('after', required=False)

            start = time.time()
            result = []
            while True:
                result = self.log_manager.get_current_execute_log_details(after) or []
                if len(result) == 0 and time.time() - start < 30:
                    time.sleep(0.1)
                else:
                    break
        except Exception as e:
            log.error("An error has occurred", exception=str(e))
            raise falcon.HTTPInternalServerError(title='A server has encountered an error', description=str(e))

        resp.json = {'is_running': self.log_manager.is_running(), 'logs': result}


# noinspection PyUnusedLocal
class ExecuteCall(object):
    def __init__(self, engine_runner):
        """
        :type engine_runner: EngineRunner
        """
        self.engine_runner = engine_runner

    def on_post(self, req, resp):
        try:
            params = {}
            req.get_param_as_list('ids', transform=int, store=params)
            req.get_param_as_list('statuses', transform=Status.parse, store=params)
            req.get_param('tracker', store=params)
            if len(params) > 1:
                raise falcon.HTTPBadRequest("wrong params count",
                                            'Only one of params are supported: ids, statuses or tracker, ' +
                                            'but {0} was provided'.format(', '.join(params.keys())))
            if 'ids' in params:
                ids = params['ids']
            elif 'statuses' in params:
                ids = self.engine_runner.trackers_manager.get_status_topics_ids(params['statuses'])
            elif 'tracker' in params:
                topics = self.engine_runner.trackers_manager.get_tracker_topics(params['tracker'])
                ids = [topic.id for topic in topics]
            else:
                ids = None
            if ids is not None and len(ids) == 0:
                raise falcon.HTTPConflict("Can't get any ids", "This request doesn't produce any topics for execute")
            self.engine_runner.execute(ids)
        except Exception as e:
            log.error("An error has occurred", exception=str(e))
            raise
