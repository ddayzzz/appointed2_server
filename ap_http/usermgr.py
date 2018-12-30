# coding=utf-8
__author__ = 'Shu Wang <wangshu214@live.cn>'
__version__ = '0.0.0.1'
__all__ = ['UserAuthMiddleware']
__doc__ = 'Appointed2 - defined some basic methods for authorizing user'
from time import time

import hashlib
from ap_http.middlewares import Middleware
from ap_logger.logger import make_logger


_logger = make_logger('MIDWARE')


class UserAuthMiddleware(Middleware):

    def __init__(self, cookie_name, cookie_key, type_of_user, dbmgr):
        """
        UserAuth ctor
        :param cookie_name: cookie name for auth user
        :param cookie_key: cookie's key
        :param type_of_user: user object which stored in ap_database, must be derived class of orm.Model and its primary key's name is id
        :param dbmgr: ap_database manager, must be instance of DatabaseManager
        :return:
        """
        self.cookie_name = cookie_name
        self.cookie_key = cookie_key
        self.type_of_user = type_of_user
        self.dbmgr = dbmgr
        super(UserAuthMiddleware, self).__init__()

    async def decode(self, cookie_str):
        """
        decode cookie to user string(basic use)
        :param cookie_str: cookie str to decode
        :return:
        """
        if not cookie_str:
            return None
        L = cookie_str.split('-')
        if len(L) != 3:
            return None
        uid, expires, sha1 = L
        if int(expires) < time():
            return None
        user = await self.dbmgr.query(self.type_of_user, id=uid)
        if user is None:
            return None
        s = '%s-%s-%s-%s' % (uid, user.passwd, expires, self.cookie_key)
        if sha1 != hashlib.sha1(s.encode('utf-8')).hexdigest():
            return None
        user.passwd = '******'  # hide the password
        return user

    async def __call__(self, request, handler):
        request.__user__ = None
        cookie_str = request.cookies.get(self.cookie_name)
        user = ''
        if cookie_str:
            if 'deleted' not in cookie_str:
                user = await self.decode(cookie_str)
            if user:
                request.__user__ = user
                _logger.debug('Set user from cookie \'%s\'' % cookie_str)
        return await handler(request)