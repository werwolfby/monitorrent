import falcon
from falcon.testing import TestBase, TestResource
from monitorrent.rest import create_api, no_auth, AuthMiddleware


class TestAuthMiddleware(TestBase):
    @classmethod
    def setUpClass(cls):
        super(TestAuthMiddleware, cls).setUpClass()
        AuthMiddleware.init('secret!', 'monitorrent')
        cls.auth_token_verified = 'eyJhbGciOiJIUzI1NiJ9.Im1vbml0b3JyZW50Ig.95p-fZYKe6CjaUbf7-gw2JKXifsocYf0w52rj-U7vHw'
        cls.auth_token_tampared = 'eyJhbGciOiJIUzI1NiJ9.Im1vbml0b3JyZW5UIg.95p-fZYKe6CjaUbf7-gw2JKXifsocYf0w52rj-U7vHw'

    def setUp(self):
        super(TestAuthMiddleware, self).setUp()
        self.api = create_api()

    def get_cookie(self, modify=False):
        token = self.auth_token_tampared if modify else self.auth_token_verified
        if modify:
            token = token
        return AuthMiddleware.cookie_name + '=' + token + '; HttpOnly; Path=/'

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
