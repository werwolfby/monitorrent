# coding=utf-8
import json
import requests
from sqlalchemy import Column, String, Integer, ForeignKey
from monitorrent.plugin_managers import register_plugin
from monitorrent.plugins.notifiers import NotificationException, NotifierPlugin, Notifier, NotifierType

PLUGIN_NAME = 'pushover'


class PushoverException(NotificationException):
    pass


class PushoverSettings(Notifier):
    __tablename__ = "pushover_settings"

    id = Column(Integer, ForeignKey('notifiers.id'), primary_key=True)

    user_id = Column(Integer, nullable=True)
    access_token = Column(String, nullable=True)

    __mapper_args__ = {
        'polymorphic_identity': PLUGIN_NAME
    }


class PushoverNotifierPlugin(NotifierPlugin):
    settings_fields = ['user_id', 'access_token']
    form = [{
        'type': 'row',
        'content': [{
            'type': 'text',
            'label': 'Use ID',
            'model': 'user_id',
            'flex': 50
        }, {
            'type': 'text',
            'label': 'Access token',
            'model': 'access_token',
            'flex': 50
        }]
    }]

    @property
    def settings_class(self):
        return PushoverSettings

    @property
    def get_type(self):
        return NotifierType.short_text

    def notify(self, header, body, url=None):
        settings = self.get_settings()
        if not settings or not settings.access_token or not settings.user_id:
            raise PushoverException(1, "Access Token or User Id was not specified")
        parameters = {
            u'token': settings.access_token,
            u'title': header,
            u'message': body,
            u'url': url,
            u'user': settings.user_id,
            u'key': settings.access_token
        }

        request = requests.post('https://api.pushover.net/1/messages.json', data=parameters)

        if request.status_code != 200:
            raise PushoverException(2, 'Failed to send Pushover notification')
        return True


register_plugin('notifier', 'pushover', PushoverNotifierPlugin())
