import falcon
import six
from monitorrent.settings_manager import SettingsManager


# noinspection PyUnusedLocal
class SettingsNotifyOn(object):
    def __init__(self, settings_manager):
        """
        :type settings_manager: SettingsManager
        """
        self.settings_manager = settings_manager

    def on_get(self, req, resp):
        resp.json = self.settings_manager.get_external_notifications_levels()

    def on_put(self, req, resp):
        if req.json is None or len(req.json) == 0:
            raise falcon.HTTPBadRequest('BodyRequired', 'Expecting not empty JSON body')

        if not isinstance(req.json, list) or any([not isinstance(i, six.text_type) for i in req.json]):
            raise falcon.HTTPBadRequest('ArrayOfStringExpected', 'Expecting list of string values')

        existing_levels = self.settings_manager.get_existing_external_notifications_levels()
        unknown_levels = [l for l in req.json if l not in existing_levels]

        if len(unknown_levels) > 0:
            raise falcon.HTTPBadRequest('UnknownLevels', '{0} are unknow levels'.format(unknown_levels))

        self.settings_manager.set_external_notifications_levels(req.json)

        resp.status = falcon.HTTP_NO_CONTENT
