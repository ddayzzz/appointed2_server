# coding=utf-8
__author__ = 'Shu Wang <wangshu214@live.cn>'
__version__ = '0.0.0.1'
__all__ = []
__doc__ = 'Appointed2 - defined some basic middlewares for ap_http server'


from aiohttp.web import middleware
from ap_http.usermgr import UserAuth
from ap_logger.logger import make_logger
import json


logger = make_logger('MIDWARE')


def make_auth_middleware(cookie_name, auth_obj):
    """
    make a basic user auth middleware
    :param auth_obj: UserAuth or its derived class
    :return:
    """
    if not isinstance(auth_obj, UserAuth):
        raise ValueError("'auth_obj' must be instance of UserAuth")


    @middleware
    async def authorization_middleware(request, handler):
        """
        middleware for auth user
        :param request: request object
        :param handler: handler passed by server
        :return: handled result
        """
        request.__user__ = None
        cookie_str = request.cookies.get(cookie_name)
        user = ''
        if cookie_str:
            if 'deleted' not in cookie_str:
                user = await auth_obj.decode(cookie_str)
            if user:
                request.__user__ = user
                logger.debug('Set user from cookie \'%s\'' % cookie_str)
        return (await handler(request))
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


def make_response_middleware():
    """
    用于处理处理器返回的数据，同时对结果、或者错误进行最终的处理
    :param app: 网页服务器实例
    :param handler: 路由处理器
    :return: 返回一个封装的可调用对象
    """
    import traceback
    from aiohttp.web import Response, StreamResponse, HTTPFound, HTTPError

    @middleware
    async def response(request, handler):
        try:
            r = await handler(request)
            # finished handle response
            if isinstance(r, Response):
                return r  # 直接返回响应
            if isinstance(r, StreamResponse):
                # 字节流。客户端默认下载的是字节流(header是application/octet-stream)。需要修改请求的类型
                accept_type = request.headers.get('accept')
                if accept_type:
                    last_com = accept_type.find(',')
                    if last_com > 0:
                        r.content_type = accept_type[:last_com]
                return r
            if isinstance(r, bytes):
                resp = Response(body=r)
                resp.content_type = 'application/octet-stream'
                return resp
            if isinstance(r, str):
                if r.startswith('redirect:'):
                    return HTTPFound(r[9:])
                resp = Response(body=r.encode('utf-8'))
                resp.content_type = 'text/html;charset=utf-8'
                return resp
            if isinstance(r, dict):
                if r.get('__template__'):
                    resp = Response(
                        body=request.app.template.get_template(r['__template__']).render(**r).encode('utf-8'))
                    resp.content_type = 'text/html;charset=utf-8'
                    return resp
                else:
                    resp = Response(
                        body=json.dumps(r, ensure_ascii=False, default=lambda o: o.__dict__()).encode('utf-8'))
                    resp.content_type = 'application/json;charset=utf-8'
                    return resp
            if isinstance(r, int) and r >= 100 and r < 600:  # 这个是保留的响应代码。有的可能需要
                return Response(status=r, text="Status: %d" % r)
            # default:
            resp = Response(body=str(r).encode('utf-8'))
            resp.content_type = 'text/plain;charset=utf-8'
            return resp
            # 由于 websocket 可能返回特殊的响应，如果这种情况，系统会自动处理
        except HTTPError as e:
            logger.error("Faild to handle request, with exception : '{0}', status: {1}".format(e, e.status), exc_info=True, stack_info=False)
    return response  # 处理完成 现在都是Response的对象 接下来就有路由关联的函数处理，也就是ResponseHandler