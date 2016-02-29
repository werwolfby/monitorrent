import falcon
import time
from monitorrent.engine import ExecuteLogManager


# noinspection PyUnusedLocal
class ExecuteLogsDetails(object):
    def __init__(self, log_manager):
        """
        :type log_manager: ExecuteLogManager
        """
        self.log_manager = log_manager

    def on_get(self, req, resp, execute_id):
        if execute_id is None or not execute_id.isdigit():
            raise falcon.HTTPBadRequest("wrong execute_id", "execute_id schould be specified and schould be int")

        execute_id = int(execute_id)

        after = req.get_param_as_int('after', required=False)

        if after is not None:
            start = time.time()
            result = []
            while True:
                result = self.log_manager.get_execute_log_details(execute_id, after) or []
                if len(result) == 0 and time.time() - start < 30 and self.log_manager.is_running(execute_id):
                    time.sleep(0.1)
                else:
                    break
        else:
            result = self.log_manager.get_execute_log_details(execute_id)

        resp.json = {'is_running': self.log_manager.is_running(), 'logs': result}
