# coding=utf-8
__author__ = 'Shu Wang <wangshu214@live.cn>'
__version__ = '0.0.0.1'
__all__ = ['Middleware', 'ResponseMiddleware', 'make_auth_middleware', 'make_data_middleware', 'make_response_middleware']
__doc__ = 'Appointed2 - defined some basic middlewares for ap_http server'


from aiohttp.web import middleware, Response, StreamResponse, HTTPFound, HTTPError, HTTPNotFound
from ap_logger.logger import make_logger
from ap_http import exceptions
from abc import abstractmethod
import json
import hashlib
import traceback
from time import time


_midware_logger = make_logger('MIDWARE')
_response_handler_logger = make_logger('RESPOSE')


class Middleware(object):

    def __init__(self, *args, **kwargs):
        pass

    @abstractmethod
    async def __call__(self, *args, **kwargs):
        pass


def make_auth_middleware(auth_obj):
    """
    make a basic user auth middleware
    :param auth_obj: Middleware or its derived class
    :return:
    """
    if not isinstance(auth_obj, Middleware):
        raise ValueError("'auth_obj' must be instance of Middleware")
    @middleware
    async def authorization_middleware(request, handler):
        return await auth_obj(request=request, handler=handler)
    return authorization_middleware


def make_data_middleware():

    @middleware
    async def data_preprocessor_middleware(request, handler):

        if request.method == 'POST':
            # 检查HTTP头的Content-Type
            if request.content_type.startswith('application/json'):
                request.__data__ = await request.json()  # 格式化为JSON
                _midware_logger.debug("Preprocess data from content type: '%s'" % request.content_type)
            elif request.content_type.startswith('application/x-www-form-urlencoded'):
                request.__data__ = await request.post()  # 这个是表格的
                _midware_logger.debug("Preprocess data from content type: '%s'" % request.content_type)

        return (await handler(request))
    return data_preprocessor_middleware


def make_response_middleware(response_middleware_obj):
    """
    middleware for different response handler
    :param response_middleware_obj:
    :return:
    """
    @middleware
    async def response_middleware(request, handler):
        return (await response_middleware_obj(request=request, handler=handler))
    return response_middleware


class ResponseMiddleware(Middleware):

    def __init__(self, *args, **kwargs):
        super(ResponseMiddleware, self).__init__()

    def _handle_response(self, request, response):
        """
        handle web response object
        :param response: response object
        :return: response
        """
        return response

    def _handle_stream_response(self, request, response):
        """
        handle stream response
        :param request:
        :param response:
        :return:
        """
        # 字节流。客户端默认下载的是字节流(header是application/octet-stream)。需要修改请求的类型
        accept_type = request.headers.get('accept')
        if accept_type:
            last_com = accept_type.find(',')
            if last_com > 0:
                response.content_type = accept_type[:last_com]
        return response

    def _handle_bytes(self, request, response):
        """
        handle bytes
        :param request:
        :param response:
        :return:
        """
        resp = Response(body=response)
        resp.content_type = 'application/octet-stream'
        return resp

    def _handle_string(self, request, response):
        """
        handle string or redirect info
        :param request:
        :param response:
        :return:
        """
        if response.startswith('redirect:'):
            return HTTPFound(response[9:])
        resp = Response(body=response.encode('utf-8'))
        resp.content_type = 'text/html;charset=utf-8'
        return resp

    def _handle_dict(self, request, response, status=200):
        """
        handle dict which will be Html Response or json response
        :param request:
        :param response:
        :param status: default status for this response
        :return:
        """
        if response.get('__template__'):
            resp = Response(
                body=request.app.template.get_template(response['__template__']).render(**response).encode('utf-8'), status=status)
            resp.content_type = 'text/html;charset=utf-8'
            return resp
        else:
            resp = Response(
                body=json.dumps(response, ensure_ascii=False, default=lambda o: self._dump_json_hook(o)).encode('utf-8'), status=status)
            resp.content_type = 'application/json;charset=utf-8'
            return resp

    def _handle_list_tuple(self, request, response, status=200):
        """
        default handler for list and tuple
        :param request:
        :param response:
        :param status:
        :return:
        """
        resp = Response(
            body=json.dumps(response, ensure_ascii=False, default=lambda o: self._dump_json_hook(o)).encode('utf-8'),
            status=status)
        resp.content_type = 'application/json;charset=utf-8'
        return resp

    def _handle_set(self, request, response, status=200):
        """
        default handler for set
        :param request:
        :param response:
        :param status:
        :return:
        """
        resp = Response(
            body=json.dumps(response, ensure_ascii=False, default=lambda o: self._dump_json_hook(o)).encode('utf-8'),
            status=status)
        resp.content_type = 'application/json;charset=utf-8'
        return resp

    def _handle_int(self, request, response):
        """
        handle int whch indicates response status
        :param request:
        :param response:
        :return:
        """
        return self._handle_dict(request=request, response={'status': response})

    def _handle_default(self, request, response):
        """
        default handler
        :param request:
        :param response:
        :return:
        """
        resp = Response(body=str(response).encode('utf-8'))
        resp.content_type = 'text/plain;charset=utf-8'
        return resp

    def _handle_server_exception(self, request, exc):
        """
        handle server exception whose status is 4xx or 5xx
        :param request:
        :param response:
        :param exc:
        :return:
        """
        return self._handle_dict(request=request, response={'status': exc.status}, status=exc.status)

    def _handle_route_exception(self, request, exc):
        """
        handle router exception and return a dict for detail of the exception
        :param request:
        :param exc:
        :return:
        """
        return self._handle_dict(request=request, response={
            'exception': '{0}'.format(type(exc)),
            'args': '\n'.join([str(x) for x in exc.args]),
            'traceback': traceback.format_exc(),
            # 'stack_info': traceback.format_stack(),
            'status': 500
        }, status=500)

    def _dump_json_hook(self, obj):
        """
        when serialize object into json object, this is hook for dumping obj
        :param obj: object to dump
        :return: serialize-able obj
        """
        return obj.__dict__()

    async def __call__(self, request, handler):
        try:
            r = await handler(request)
            # finished handle response
            if isinstance(r, Response):
                return self._handle_response(request=request, response=r)
            if isinstance(r, StreamResponse):
                return self._handle_stream_response(request=request, response=r)
            if isinstance(r, bytes):
                return self._handle_bytes(request=request, response=r)
            if isinstance(r, str):
                return self._handle_string(request=request, response=r)
            if isinstance(r, dict):
                return self._handle_dict(request=request, response=r)
            if isinstance(r, (tuple, list)):
                return self._handle_list_tuple(request=request, response=r)
            if isinstance(r, set):
                return self._handle_set(request=request, response=r)
            if isinstance(r, int) and r >= 100 and r < 600:  # 这个是保留的响应代码。有的可能需要
                return self._handle_int(request=request, response=r)
            # default:
            return self._handle_default(request=request, response=r)
            # 由于 websocket 可能返回特殊的响应，如果这种情况，系统会自动处理
        except HTTPNotFound as e:
            # hide error info which will be present in aiohttp.access
            # _response_handler_logger.error(
            #     'Not found : {0} {1}'.format(request.method, request.path_qs),
            #     exc_info=False, stack_info=False)
            return self._handle_server_exception(request=request.method, exc=e)
        except HTTPError as e:
            # hide error info which will be present in aiohttp.access
            # _response_handler_logger.error("Faild to handle request, with exception : '{0}', status: {1}".format(e, e.status),
            #              exc_info=True, stack_info=False)
            return self._handle_server_exception(request=request, exc=e)
        except exceptions.CallbackError as e:
            _response_handler_logger.error("Can't call the route handler: {0}".format(e.message))
            return self._handle_route_exception(request=request, exc=e)
        except Exception as e:
            _response_handler_logger.error("Faild to handle request, with router's inner exception : '{0}'".format(e), exc_info=True, stack_info=False)
            return self._handle_route_exception(request=request, exc=e)


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
                try:
                    user = await self.decode(cookie_str)
                except Exception as e:
                    _midware_logger.error('Decode cookie str {0} failed, with exception: {1}'.format(cookie_str, type(e)))
                    user = ''
            if user:
                request.__user__ = user
                _midware_logger.debug('Set user from cookie \'%s\'' % cookie_str)
        return await handler(request)
