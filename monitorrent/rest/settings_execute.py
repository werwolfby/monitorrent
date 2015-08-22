import falcon


# noinspection PyUnusedLocal
class SettingsExecute(object):
    def __init__(self, engine_runner):
        self.engine_runner = engine_runner

    def on_get(self, req, resp):
        resp.json = {
            "interval": self.engine_runner.interval,
            "last_execute": self.engine_runner.last_execute
        }

    def on_put(self, req, resp):
        if req.json is None:
            raise falcon.HTTPBadRequest('BodyRequired', 'Expecting not empty JSON body')

        settings = req.json
        if 'interval' not in settings or not isinstance(settings['interval'], int):
            raise falcon.HTTPBadRequest('WrongParameter', '"interval" int value is required')

        self.engine_runner.interval = int(settings['interval'])
        resp.status = falcon.HTTP_NO_CONTENT
