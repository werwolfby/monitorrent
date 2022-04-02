from builtins import object
# coding=utf-8


class RutrackerHelper(object):
    # real values
    real_login = None
    real_password = None
    real_uid = None
    real_bb_data = None
    # fake values
    fake_login = 'fakelogin'
    fake_password = 'p@$$w0rd'
    fake_uid = '15564713'
    fake_bb_data = '0-4301487-0jwgwpFKGYFDp6Ye6yne'

    def __init__(self, login=None, password=None, uid=None, bb_data=None):
        self.real_login = login or self.fake_login
        self.real_password = password or self.fake_password
        self.real_uid = uid or self.fake_uid
        self.real_bb_data = bb_data or self.fake_bb_data
