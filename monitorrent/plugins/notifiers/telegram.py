# coding=utf-8
import json
import requests
from sqlalchemy import Column, String, Integer, ForeignKey
from monitorrent.plugin_managers import register_plugin
from monitorrent.plugins.notifiers import NotificationException, NotifierPlugin, Notifier

PLUGIN_NAME = 'telegram'


class TelegramException(NotificationException):
    pass


class TelegramSettings(Notifier):
    __tablename__ = "telegram_settings"

    id = Column(Integer, ForeignKey('notifiers.id'), primary_key=True)

    chat_id = Column(Integer, nullable=True)
    access_token = Column(String, nullable=True)

    __mapper_args__ = {
        'polymorphic_identity': PLUGIN_NAME
    }


class TelegramNotifierPlugin(NotifierPlugin):
    _telegram_api_format = 'https://api.telegram.org/bot{0}/{1}'

    form = [{
        'type': 'row',
        'content': [{
            'type': 'text',
            'label': 'Chat ID',
            'model': 'chat_id',
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
        return TelegramSettings

    def notify(self, header, body, url=None):
        settings = self.get_settings()
        if not settings or not settings.access_token or not settings.chat_id:
            raise TelegramException(1, "Access Token or User Id was not specified")
        api_url = self._telegram_api_format.format(settings.access_token, 'sendMessage')
        text = header + '\n\n' + body
        if url:
            text = text + '\n' + url
        parameters = {
            u'chat_id': settings.chat_id,
            u'text': text,
        }

        request = requests.post(api_url, data=parameters)

        if request.status_code != 200:
            raise TelegramException(2, 'Failed to send Telegram notification')
        return True


register_plugin('notifier', 'telegram', TelegramNotifierPlugin())
