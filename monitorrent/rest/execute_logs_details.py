import falcon
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

        resp.json = self.log_manager.get_execute_log_details(execute_id)
