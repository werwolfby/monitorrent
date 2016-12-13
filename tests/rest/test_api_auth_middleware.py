import falcon
from falcon.testing import TestResource
from tests import RestTestBase
from monitorrent.rest import no_auth, AuthMiddleware


def is_auth_enabled():
    return False


class TestAuthMiddleware(RestTestBase):
    def setUp(self, disable_auth=False):
        super(TestAuthMiddleware, self).setUp(disable_auth)

    def test_auth_success(self):
        self.api.add_route(self.test_route, TestResource())

        self.simulate_request(self.test_route, headers={'Cookie': self.get_cookie()})
        self.assertEqual(falcon.HTTP_OK, self.srmock.status)

    def test_no_auth_success(self):
        self.api.add_route(self.test_route, no_auth(TestResource()))

        self.simulate_request(self.test_route)
        self.assertEqual(falcon.HTTP_OK, self.srmock.status)

    def test_authenticate(self):
        resp = falcon.Response()
        AuthMiddleware.authenticate(resp)

        self.assertIsNotNone(resp._cookies)
        jwt = resp._cookies[AuthMiddleware.cookie_name]

        self.assertEqual(jwt.key, AuthMiddleware.cookie_name)
        self.assertEqual(jwt.value, self.auth_token_verified)
        self.assertEqual(jwt['path'], '/')

    def test_auth_failed_without_cookie(self):
        self.api.add_route(self.test_route, TestResource())

        self.simulate_request(self.test_route)
        self.assertEqual(falcon.HTTP_UNAUTHORIZED, self.srmock.status)

    def test_auth_failed_with_modified_cookie(self):
        self.api.add_route(self.test_route, TestResource())

        self.simulate_request(self.test_route, headers={'Cookie': self.get_cookie(True)})
        self.assertEqual(falcon.HTTP_UNAUTHORIZED, self.srmock.status)

    def test_auth_failed_with_random_cookie(self):
        self.api.add_route(self.test_route, TestResource())

        self.simulate_request(self.test_route, headers={'Cookie': 'jwt=random; HttpOnly; Path=/'})
        self.assertEqual(falcon.HTTP_UNAUTHORIZED, self.srmock.status)

    def test_disabled_auth(self):
        self.api.add_route(self.test_route, TestResource())
        AuthMiddleware.init('secret!', 'monitorrent', is_auth_enabled)
        self.simulate_request(self.test_route, headers={'Cookie': 'jwt=random; HttpOnly; Path=/'})

        self.assertEqual(falcon.HTTP_OK, self.srmock.status)
