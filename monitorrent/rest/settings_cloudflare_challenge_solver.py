import falcon
import six
from monitorrent.settings_manager import SettingsManager
from monitorrent.new_version_checker import NewVersionChecker


# noinspection PyUnusedLocal
class SettingsCloudflareChallengeSolver(object):
    def __init__(self, settings_manager):
        """
        :type settings_manager: SettingsManager
        """
        self.settings_manager = settings_manager

    def on_get(self, req, resp):
        resp.json = {
            'debug': self.settings_manager.cloudflare_challenge_solver_debug,
            'record_video': self.settings_manager.cloudflare_challenge_solver_record_video,
            'record_har': self.settings_manager.cloudflare_challenge_solver_record_har,
            'keep_records': self.settings_manager.cloudflare_challenge_solver_keep_records,
        }

    def on_patch(self, req, resp):
        if req.json is None or len(req.json) == 0:
            raise falcon.HTTPBadRequest('BodyRequired', 'Expecting not empty JSON body')

        debug = req.json.get('debug')
        if debug is not None and not isinstance(debug, bool):
            raise falcon.HTTPBadRequest('WrongValue', '"debug" have to be bool')

        record_video = req.json.get('record_video')
        if record_video is not None and not isinstance(record_video, bool):
            raise falcon.HTTPBadRequest('WrongValue', '"record_video" have to be bool')

        record_har = req.json.get('record_har')
        if record_har is not None and not isinstance(record_har, bool):
            raise falcon.HTTPBadRequest('WrongValue', '"record_har" have to be bool')

        keep_records = req.json.get('keep_records')
        if keep_records is not None and not isinstance(keep_records, int):
            raise falcon.HTTPBadRequest('WrongValue', '"keep_records" have to be int')

        if debug is not None:
            if self.settings_manager.cloudflare_challenge_solver_debug != debug:
                self.settings_manager.cloudflare_challenge_solver_debug = debug

        if record_video is not None:
            if self.settings_manager.cloudflare_challenge_solver_record_video != record_video:
                self.settings_manager.cloudflare_challenge_solver_record_video = record_video

        if record_har is not None:
            if self.settings_manager.cloudflare_challenge_solver_record_har != record_har:
                self.settings_manager.cloudflare_challenge_solver_record_har = record_har

        if keep_records is not None:
            if self.settings_manager.cloudflare_challenge_solver_keep_records != keep_records:
                self.settings_manager.cloudflare_challenge_solver_keep_records = keep_records

        resp.status = falcon.HTTP_NO_CONTENT
