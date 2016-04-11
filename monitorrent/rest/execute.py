from builtins import object
import time
from monitorrent.engine import EngineRunner, ExecuteLogManager


# noinspection PyUnusedLocal
class ExecuteLogCurrent(object):
    def __init__(self, log_manager):
        """
        :type log_manager: ExecuteLogManager
        """
        self.log_manager = log_manager

    def on_get(self, req, resp):
        after = req.get_param_as_int('after', required=False)

        start = time.time()
        result = []
        while True:
            result = self.log_manager.get_current_execute_log_details(after) or []
            if len(result) == 0 and time.time() - start < 30:
                time.sleep(0.1)
            else:
                break

        resp.json = {'is_running': self.log_manager.is_running(), 'logs': result}


# noinspection PyUnusedLocal
class ExecuteCall(object):
    def __init__(self, engine_runner):
        """
        :type engine_runner: EngineRunner
        """
        self.engine_runner = engine_runner

    def on_post(self, req, resp):
        ids = req.get_param_as_list('ids', transform=int)
        self.engine_runner.execute(ids)
