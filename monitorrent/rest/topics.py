from builtins import str
from builtins import object
import falcon
import six
from monitorrent.plugin_managers import TrackersManager


# noinspection PyUnusedLocal
class TopicCollection(object):
    def __init__(self, tracker_manager):
        """
        :type tracker_manager: TrackersManager
        """
        self.tracker_manager = tracker_manager

    def on_get(self, req, resp):
        resp.json = self.tracker_manager.get_watching_topics()

    def on_post(self, req, resp):
        body = req.json
        try:
            url = body['url']
            settings = body['settings']
            added = self.tracker_manager.add_topic(url, settings)
        except KeyError:
            raise falcon.HTTPBadRequest('WrongParameters', 'Can\'t add topic')
        if not added:
            raise falcon.HTTPInternalServerError('ServerError', 'Can\'t add topic')
        resp.status = falcon.HTTP_201


class TopicParse(object):
    def __init__(self, tracker_manager):
        """
        :type tracker_manager: TrackersManager
        """
        self.tracker_manager = tracker_manager

    def on_get(self, req, resp):
        url = six.text_type(req.get_param('url', required=True))
        title = self.tracker_manager.prepare_add_topic(url)
        if not title:
            raise falcon.HTTPBadRequest('CantParse', 'Can\'t parse url: \'{}\''.format(url))
        resp.json = title


# noinspection PyUnusedLocal,PyShadowingBuiltins
class Topic(object):
    def __init__(self, tracker_manager):
        """
        :type tracker_manager: TrackersManager
        """
        self.tracker_manager = tracker_manager

    def on_get(self, req, resp, id):
        try:
            topic = self.tracker_manager.get_topic(id)
        except KeyError as e:
            raise falcon.HTTPNotFound(title='Id {0} not found'.format(id), description=str(e))
        resp.json = topic

    def on_put(self, req, resp, id):
        settings = req.json
        try:
            updated = self.tracker_manager.update_topic(id, settings)
        except KeyError as e:
            raise falcon.HTTPNotFound(title='Id {0} not found'.format(id), description=str(e))
        if not updated:
            raise falcon.HTTPInternalServerError('ServerError', 'Can\'t update topic {}'.format(id))
        resp.status = falcon.HTTP_204

    def on_delete(self, req, resp, id):
        try:
            deleted = self.tracker_manager.remove_topic(id)
        except KeyError as e:
            raise falcon.HTTPNotFound(title='Id {0} not found'.format(id), description=str(e))
        if not deleted:
            raise falcon.HTTPInternalServerError('ServerError', 'Can\'t delete topic {}'.format(id))
        resp.status = falcon.HTTP_204


# noinspection PyUnusedLocal,PyShadowingBuiltins
class TopicResetStatus(object):
    def __init__(self, tracker_manager):
        """
        :type tracker_manager: TrackersManager
        """
        self.tracker_manager = tracker_manager

    def on_post(self, req, resp, id):
        try:
            updated = self.tracker_manager.reset_topic_status(id)
        except KeyError as e:
            raise falcon.HTTPNotFound(title='Id {0} not found'.format(id), description=str(e))
        if not updated:
            raise falcon.HTTPInternalServerError('ServerError', 'Can\'t reset topic {} status'.format(id))
        resp.status = falcon.HTTP_204
