from monitorrent.engine import ExecuteLogManager


# noinspection PyUnusedLocal
class ExecuteLogs(object):
    def __init__(self, log_manager):
        """
        :type log_manager: ExecuteLogManager
        """
        self.log_manager = log_manager

    def on_get(self, req, resp):
        take = req.get_param_as_int('take', required=True, min=1, max=100)
        skip = req.get_param_as_int('skip', required=False, min=0) or 0

        executes, count = self.log_manager.get_log_entries(skip, take)

        resp.json = {
            'data': executes,
            'count': count
        }
