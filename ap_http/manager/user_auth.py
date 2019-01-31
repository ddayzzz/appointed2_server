# coding=utf-8
from ap_http.middlewares import Middleware
from ap_logger.logger import make_logger
import hashlib
from time import time
__author__ = 'Shu Wang <wangshu214@live.cn>'
__version__ = '0.0.0.1'
__all__ = ['UserAuthMiddleware']
__doc__ = 'Appointed2 - a basic user auth middleware for back of a website'


_auth_handler_logger = make_logger('USER-AUTH')


class UserAuthMiddleware(Middleware):

    def __init__(self, cookie_name, cookie_key, type_of_user, where_field:str, dbmgr):
        """
        UserAuth ctor
        :param cookie_name: cookie name for auth user
        :param cookie_key: cookie's key
        :param type_of_user: user object which stored in ap_database, must be derived class of orm.Model
        :param where_field: a query field that will have only one result. e.g. uid=?
        :param dbmgr: ap_database manager, must be instance of DatabaseManager
        :return:
        """
        self.cookie_name = cookie_name
        self.cookie_key = cookie_key
        self.type_of_user = type_of_user
        self.dbmgr = dbmgr
        self.where_field = where_field
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
        user = await self.dbmgr.queryAll(self.type_of_user, sql_where=self.where_field, args=(uid, ))
        if user is None or len(user) != 1:
            return None
        user = user[0]
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
                try:
                    user = await self.decode(cookie_str)
                except Exception as e:
                    _auth_handler_logger.error('Decode cookie str {0} failed, with exception: {1}'.format(cookie_str, type(e)))
                    user = ''
            if user:
                request.__user__ = user
                _auth_handler_logger.debug('Set user from cookie \'%s\'' % cookie_str)
        return await handler(request)
