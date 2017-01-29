from builtins import str
from builtins import object
import falcon
from monitorrent.plugin_managers import TrackersManager
from monitorrent.plugins.trackers import WithCredentialsMixin


# noinspection PyUnusedLocal
class TrackerCollection(object):
    def __init__(self, tracker_manager):
        """
        :type tracker_manager: TrackersManager
        """
        self.tracker_manager = tracker_manager

    def on_get(self, req, resp):
        resp.json = [{'name': name, 'form': tracker.credentials_form if hasattr(tracker, 'credentials_form') else None}
                     for name, tracker in list(self.tracker_manager.trackers.items())]


# noinspection PyUnusedLocal
class Tracker(object):
    def __init__(self, tracker_manager):
        """
        :type tracker_manager: TrackersManager
        """
        self.tracker_manager = tracker_manager

    def on_get(self, req, resp, tracker):
        try:
            tracker_plugin = self.tracker_manager.get_tracker(tracker)
            settings = self.tracker_manager.get_settings(tracker)
            if not settings:
                settings = {}
            result = {
                'can_check': isinstance(tracker_plugin, WithCredentialsMixin),
                'settings': settings
            }
        except KeyError as e:
            raise falcon.HTTPNotFound(title='Tracker plugin \'{0}\' not found'.format(tracker), description=str(e))
        resp.json = result

    def on_put(self, req, resp, tracker):
        settings = req.json
        try:
            updated = self.tracker_manager.set_settings(tracker, settings)
        except KeyError as e:
            raise falcon.HTTPNotFound(title='Tracker plugin \'{0}\' not found'.format(tracker), description=str(e))
        if not updated:
            raise falcon.HTTPBadRequest('NotSettable', 'Tracker plugin \'{0}\' doesn\'t support settings'
                                        .format(tracker))
        resp.status = falcon.HTTP_NO_CONTENT


# noinspection PyUnusedLocal
class TrackerCheck(object):
    def __init__(self, tracker_manager):
        """
        :type tracker_manager: TrackersManager
        """
        self.tracker_manager = tracker_manager

    def on_get(self, req, resp, tracker):
        try:
            resp.json = {'status': True if self.tracker_manager.check_connection(tracker) else False}
        except KeyError as e:
            raise falcon.HTTPNotFound(title='Tracker plugin \'{0}\' not found'.format(tracker), description=str(e))
        resp.status = falcon.HTTP_OK
