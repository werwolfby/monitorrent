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
    fake_bb_data = '1-15564713-ELKc8t23nmllV4gydkNx-634753855-1440364056-1440408614-2609875527-0'

    def __init__(self, login=None, password=None, uid=None, bb_data=None):
        self.real_login = login or self.fake_login
        self.real_password = password or self.fake_password
        self.real_uid = uid or self.fake_uid
        self.real_bb_data = bb_data or self.fake_bb_data
