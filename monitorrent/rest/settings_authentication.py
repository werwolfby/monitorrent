from monitorrent.settings_manager import SettingsManager


# noinspection PyUnusedLocal
class SettingsAuthentication(object):
    def __init__(self, settings_manager):
        """
        :type settings_manager: SettingsManager
        """
        self.settings_manager = settings_manager

    def on_get(self, req, resp):
        resp.json = {'is_authentication_enabled': self.settings_manager.get_is_authentication_enabled()}
