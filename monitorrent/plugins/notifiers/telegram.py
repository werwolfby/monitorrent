# coding=utf-8
import re
import requests
from sqlalchemy import Column, Integer, String, MetaData, Table, ForeignKey
from monitorrent.plugin_managers import register_plugin
from monitorrent.plugins.notifiers import NotificationException, NotifierPlugin, Notifier, NotifierType

PLUGIN_NAME = 'telegram'


class TelegramException(NotificationException):
    pass


class TelegramSettings(Notifier):
    __tablename__ = "telegram_settings"

    id = Column(Integer, ForeignKey('notifiers.id'), primary_key=True)
    chat_ids = Column(String, nullable=True)
    access_token = Column(String, nullable=True)

    __mapper_args__ = {
        'polymorphic_identity': PLUGIN_NAME
    }


# noinspection PyUnusedLocal
def upgrade(engine, operations_factory):
    if not engine.dialect.has_table(engine.connect(), TelegramSettings.__tablename__):
        return
    version = get_current_version(engine)
    if version == 0:
        upgrade_0_to_1(engine, operations_factory)
        version = 1


def upgrade_0_to_1(engine, operations_factory):
    m0 = MetaData()
    telegram_settings_0 = Table('telegram_settings', m0,
                                Column('id', Integer, ForeignKey('notifiers.id'), primary_key=True),
                                Column('chat_id', Integer, nullable=True),
                                Column('access_token', String, nullable=True))

    m1 = MetaData()
    telegram_settings_1 = Table('telegram_settings1', m1,
                                Column('id', Integer, ForeignKey('notifiers.id'), primary_key=True),
                                Column('chat_ids', String, nullable=True),
                                Column('access_token', String, nullable=True))

    with operations_factory() as operations:
        operations.create_table(telegram_settings_1)

        credentials = operations.db.query(telegram_settings_0)
        for credential in credentials:
            credential1 = {
                'chat_ids': str(credential.chat_id),
                'access_token': credential.access_token
            }
            operations.db.execute(telegram_settings_1.insert(), credential1)

        operations.drop_table(telegram_settings_0.name)
        operations.rename_table(telegram_settings_1.name, telegram_settings_0.name)


def get_current_version(engine):
    m = MetaData(engine)
    credentials = Table(TelegramSettings.__tablename__, m, autoload=True)
    if 'chat_ids' in credentials.columns:
        return 1
    return 0


class TelegramNotifierPlugin(NotifierPlugin):
    _remove_tags_regex = re.compile(u"</?[a-z]+>", re.IGNORECASE)
    _telegram_api_format = 'https://api.telegram.org/bot{0}/{1}'

    form = [{
        'type': 'row',
        'content': [{
            'type': 'text',
            'label': 'Chat ID (comma separated chat ids)',
            'model': 'chat_ids',
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

    @property
    def get_type(self):
        return NotifierType.short_text

    def notify(self, header, body, url=None):
        settings = self.get_settings()
        if not settings or not settings.access_token or not settings.chat_ids:
            raise TelegramException(1, "Access Token or User Id was not specified")
        api_url = self._telegram_api_format.format(settings.access_token, 'sendMessage')
        text = body
        if url:
            text = text + '\n' + url
        text = self._remove_tags(text)

        chat_ids = [c.strip() for c in settings.chat_ids.split(',')]
        errors_chat_ids = None
        for chat_id in chat_ids:
            parameters = {
                u'chat_id': chat_id,
                u'text': text,
            }

            request = requests.post(api_url, data=parameters)

            if request.status_code != 200:
                if errors_chat_ids is None:
                    errors_chat_ids = []
                errors_chat_ids.append(chat_id)

        if errors_chat_ids is not None and len(errors_chat_ids) > 0:
            raise TelegramException(2, 'Failed to send Telegram notification to {0}'.format(errors_chat_ids))

        return True

    def _remove_tags(self, text):
        return self._remove_tags_regex.sub(u"", text)


register_plugin('notifier', 'telegram', TelegramNotifierPlugin(), upgrade)
