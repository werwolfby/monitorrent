import os
from builtins import object
from os import path

from monitorrent.settings_manager import SettingsManager


# noinspection PyUnusedLocal
class ChallengeLogs(object):
    def __init__(self, settings_manager):
        """
        :type settings_manager: SettingsManager
        """
        self.settings_manager = settings_manager

    def on_get(self, req, resp):
        # scan folder webapp/challenges
        challenges_folder = path.join('webapp', 'challenges')
        challenges = []
        for folder in sorted(os.listdir(challenges_folder), reverse=True):
            challenge_folder = path.join(challenges_folder, folder)
            if not os.path.isdir(challenge_folder):
                continue
            challenge = {
                'folder': folder,
                'video': self._get_video(challenge_folder),
                'har': self._get_har(challenge_folder),
            }
            challenges.append(challenge)

        resp.json = challenges

    @staticmethod
    def _get_har(challenge_folder):
        har_file = path.join(challenge_folder, 'challenge.har')
        if path.exists(har_file):
            return 'challenge.har'
        return None

    @staticmethod
    def _get_video(challenge_folder):
        video_files = os.listdir(challenge_folder)
        for video_file in video_files:
            if not video_file.endswith('.webm'):
                continue
            if path.exists(path.join(challenge_folder, video_file)):
                return video_file
        return None
