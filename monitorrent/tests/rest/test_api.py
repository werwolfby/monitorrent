import falcon
from datetime import datetime
from monitorrent.rest import MonitorrentJSONEncoder
from unittest import TestCase
from ddt import ddt, data, unpack
from monitorrent.tests import RestTestBase


@ddt
class MonitorrentJSONEncoderTest(TestCase):
    encoder = MonitorrentJSONEncoder()

    @unpack
    @data(((2015, 8, 21, 0, 53, 3), '2015-08-21T00:53:03'),
          ((2014, 12, 2, 11, 3, 31), '2014-12-02T11:03:31'))
    def test_encode_time(self, date, encoded):
        dt = datetime(*date)
        self.assertEqual(encoded, self.encoder.default(dt))

    def test_int_encode(self):
        with self.assertRaises(TypeError):
            self.assertEqual(1, self.encoder.default(1))


class MiddlewareClassResource(object):

    def on_get(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.body = {'status': 'ok'}


@ddt
class JSONTranslatorTest(RestTestBase):
    @data('\xff\xff', 'NotAJSon')
    def test_bad_request(self, body):
        self.api.add_route('/route', MiddlewareClassResource())

        self.simulate_request('/route', method='POST', body=body)

        self.assertEqual(falcon.HTTP_BAD_REQUEST, self.srmock.status)

