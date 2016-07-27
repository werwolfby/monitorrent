from builtins import object
import falcon
import six
from monitorrent.settings_manager import SettingsManager
from monitorrent.new_version_checker import NewVersionChecker


# noinspection PyUnusedLocal
class SettingsNewVersionChecker(object):
    def __init__(self, settings_manager, new_version_checker):
        """
        :type settings_manager: SettingsManager
        :type new_version_checker: NewVersionChecker
        """
        self.settings_manager = settings_manager
        self.new_version_checker = new_version_checker

    def on_get(self, req, resp):
        resp.json = {
            'enabled': self.settings_manager.get_is_new_version_checker_enabled(),
            'interval': self.settings_manager.new_version_check_interval
        }

    def on_patch(self, req, resp):
        if req.json is None or len(req.json) == 0:
            raise falcon.HTTPBadRequest('BodyRequired', 'Expecting not empty JSON body')

        enabled = req.json.get('enabled')
        if enabled is not None and not isinstance(enabled, bool):
            raise falcon.HTTPBadRequest('WrongValue', '"enabled" have to be bool')

        check_interval = req.json.get('interval')
        if check_interval is not None and not isinstance(check_interval, int):
            raise falcon.HTTPBadRequest('WrongValue', '"check_interval" have to be int')

        if enabled is not None:
            if self.settings_manager.get_is_new_version_checker_enabled() != enabled:
                self.settings_manager.set_is_new_version_checker_enabled(enabled)
        else:
            enabled = self.settings_manager.get_is_new_version_checker_enabled()

        interval_changed = False
        if check_interval is not None and self.settings_manager.new_version_check_interval != check_interval:
            self.settings_manager.new_version_check_interval = check_interval
            interval_changed = True

        if not enabled:
            self.new_version_checker.stop()
        else:
            if self.new_version_checker.is_started():
                if interval_changed:
                    self.new_version_checker.stop()
                    self.new_version_checker.start(check_interval)
            else:
                self.new_version_checker.start(check_interval)

        resp.status = falcon.HTTP_NO_CONTENT
