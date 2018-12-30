# coding=utf-8
__author__ = 'Shu Wang <wangshu214@live.cn>'
__version__ = '0.0.0.1'
__all__ = ['Middleware', 'ResponseMiddleware', 'make_auth_middleware', 'make_data_middleware', 'make_response_middleware']
__doc__ = 'Appointed2 - defined some basic middlewares for ap_http server'


from aiohttp.web import middleware, Response, StreamResponse, HTTPFound, HTTPError
from ap_logger.logger import make_logger
from abc import abstractmethod
import json
import traceback


logger = make_logger('MIDWARE')


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
                logger.debug("Preprocess data from content type: '%s'" % request.content_type)
            elif request.content_type.startswith('application/x-www-form-urlencoded'):
                request.__data__ = await request.post()  # 这个是表格的
                logger.debug("Preprocess data from content type: '%s'" % request.content_type)

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
                body=json.dumps(response, ensure_ascii=False, default=lambda o: o.__dict__()).encode('utf-8'), status=status)
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
            'args': '\n'.join(exc.args),
            'traceback': traceback.format_exc(),
            # 'stack_info': traceback.format_stack(),
            'status': 500
        }, status=500)

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
            if isinstance(r, int) and r >= 100 and r < 600:  # 这个是保留的响应代码。有的可能需要
                return self._handle_int(request=request, response=r)
            # default:
            return self._handle_default(request=request, response=r)
            # 由于 websocket 可能返回特殊的响应，如果这种情况，系统会自动处理
        except HTTPError as e:
            logger.error("Faild to handle request, with exception : '{0}', status: {1}".format(e, e.status),
                         exc_info=True, stack_info=False)
            return self._handle_server_exception(request=request, exc=e)
        except Exception as e:
            logger.error("Faild to handle request, with router's inner exception : '{0}'".format(e), exc_info=True, stack_info=False)
            return self._handle_route_exception(request=request, exc=e)
