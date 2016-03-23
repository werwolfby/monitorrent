from builtins import object
# coding=utf-8


class FreeTorrentsHelper(object):
    # real values
    real_login = None
    real_password = None
    real_uid = None
    real_bbe_data = None
    # fake values
    fake_login = 'fakelogin'
    fake_password = 'p@$$w0rd'
    fake_uid = '1038949'
    fake_bbe_data = 'a%3A3%3A%7Bs%3A2%3A%22uk%22%3BN%3Bs%3A3%3A%22uid%22%3Bi%3A1038949%3Bs%3A3%3A%22sid%22%3Bs%3A20%3A%22FmXga1i0x14z2qYmGc9A%22%3B%7D'

    def __init__(self, login=None, password=None, uid=None, bbe_data=None):
        self.real_login = login or self.fake_login
        self.real_password = password or self.fake_password
        self.real_uid = uid or self.fake_uid
        self.real_bbe_data = bbe_data or self.fake_bbe_data
