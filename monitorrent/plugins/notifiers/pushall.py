# coding=utf-8
import json
import requests
from sqlalchemy import Column, String, Integer, ForeignKey
from monitorrent.plugin_managers import register_plugin
from monitorrent.plugins.notifiers import NotificationException, NotifierPlugin, Notifier, NotifierType

PLUGIN_NAME = 'pushall'


class PushAllException(NotificationException):
    pass


class PushAllSettings(Notifier):
    __tablename__ = "push_all_settings"

    id = Column(Integer, ForeignKey('notifiers.id'), primary_key=True)

    user_id = Column(Integer, nullable=True)
    access_token = Column(String, nullable=True)

    __mapper_args__ = {
        'polymorphic_identity': PLUGIN_NAME
    }


class PushAllNotifierPlugin(NotifierPlugin):
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
    def get_type(self):
        return NotifierType.short_text

    @property
    def settings_class(self):
        return PushAllSettings

    def notify(self, header, body, url=None):
        settings = self.get_settings()
        if not settings or not settings.access_token or not settings.user_id:
            raise PushAllException(1, "Access Token or User Id was not specified")
        parameters = {
            u'type': 'self',
            u'title': header,
            u'text': body,
            u'url': url,
            u'id': settings.user_id,
            u'key': settings.access_token
        }

        request = requests.post('https://pushall.ru/api.php', data=parameters)
        result = json.loads(request.text)

        if 'error' in result:
            raise PushAllException(2, 'Failed to send PushAll notification')
        return True


register_plugin('notifier', 'pushall', PushAllNotifierPlugin())
