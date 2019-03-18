# coding=utf-8
__author__ = 'Shu Wang <wangshu214@live.cn>'
__version__ = '0.0.0.1'
__all__ = ['Middleware', 'ResponseMiddleware', 'Jinja2TemplateResponseMiddleware', 'make_middleware_wrap']
__doc__ = 'Appointed2 - defined some basic middlewares for ap_http server'


from aiohttp.web import middleware, Response, StreamResponse, HTTPFound, HTTPError, HTTPNotFound
from ap_logger.logger import make_logger
from ap_http import exceptions
from abc import abstractmethod
from functools import singledispatch
from collections import  abc
import json
import traceback



_midware_logger = make_logger('MIDWARE')
_response_handler_logger = make_logger('RESPOSE')


class Middleware(object):

    def __init__(self, *args, **kwargs):
        pass

    @abstractmethod
    async def __call__(self, *args, **kwargs):
        pass


class PrepareDataMiddleware(Middleware):

    def __init__(self, *args, **kwargs):
        super(PrepareDataMiddleware, self).__init__(*args, **kwargs)

    async def __call__(self, request, handler):
        if request.method == 'POST':
            # 检查HTTP头的Content-Type
            if request.content_type.startswith('application/json'):
                request.__data__ = await request.json()  # 格式化为JSON
                _midware_logger.debug("Preprocess data from content type: '%s'" % request.content_type)
            elif request.content_type.startswith('application/x-www-form-urlencoded'):
                request.__data__ = await request.post()  # 这个是表格的
                _midware_logger.debug("Preprocess data from content type: '%s'" % request.content_type)
        return (await handler(request))


class ResponseMiddleware(Middleware):

    def __init__(self, *args, **kwargs):
        super(ResponseMiddleware, self).__init__()


    def _handle_response(self, request, response):
        """
        handle web.response object
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
        handle dict, and return the response whose headers is applicationn/json
        :param request:
        :param response:
        :param status: default status for this response
        :return:
        """
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
        if obj and hasattr(obj, '__dict__') and callable(obj.__dict__):
            return obj.__dict__()
        else:
            return str(obj)

    @middleware
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
            return self._handle_server_exception(request=request, exc=e)
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


class Jinja2TemplateResponseMiddleware(ResponseMiddleware):

    _DEFAULT_ERROR_STRING = '<h1>{reason}</h1><br><p>Method: {method}</p><br><p>Path: {path}</p>'
    _DEFAULT_ROUTE_ERROR_STRING = '<h1>{error_class}</h1><br><pre>{traceback}</pre><p>Method: {method}</p><br><p>Path: {path}</p>'

    def __init__(self, templates_dir, filters=None, only_process_on_get=True, *args, **kwargs):
        """
        jinja2 callback. If you want to render the jinja2 template, please return dict object with '__template__' set
        :param templates_dir: root dir for jinja2 template htmls
        :param filters: the initial filters. it must be a dict whose element is name->calllback
        :param only_process_on_get: only render the template when request's method is GET
        :param args:
        :param kwargs:
        """
        super(Jinja2TemplateResponseMiddleware, self).__init__()
        # 构造 jinja2 的模板初始化部分
        from jinja2 import Environment, FileSystemLoader
        options = dict(
            autoescape=kwargs.get('autoescape', True),
            block_start_string=kwargs.get('block_start_string', '{%'),
            block_end_string=kwargs.get('block_end_string', '%}'),
            variable_start_string=kwargs.get('variable_start_string', '{{'),
            variable_end_string=kwargs.get('variable_end_string', '}}'),
            auto_reload=kwargs.get('auto_reload', True)
        )
        env = Environment(loader=FileSystemLoader(templates_dir), **options)
        if filters is not None:
            for name, f in filters.items():
                env.filters[name] = f
        self.template = env
        self.error_html = dict()
        self.route_error_html = None
        self.only_process_on_get = only_process_on_get

    def add_filter(self, name, callback):
        """
        add filter for jinja2 inner-template callback
        :param name: name, same as function name
        :param callback: function
        :return:
        """
        if self.template:
            self.template.filters[name] = callback

    def set_error_status_handle(self, error_status_code, filename):
        self.error_html[error_status_code] = filename

    def _render_template(self, doc, status, **kwargs):
        resp = Response(
            body=self.template.get_template(doc).render(**kwargs).encode('utf-8'),
            status=status)
        resp.content_type = 'text/html;charset=utf-8'
        return resp

    def _handle_dict(self, request, response, status=200):
        """
        :param request:
        :param response:
        :param status:
        :return:
        """
        if response.get('__template__'):
            return self._render_template(response['__template__'], status=status, **response)
        else:
            return super(Jinja2TemplateResponseMiddleware, self)._handle_dict(request=request, response=response, status=status)

    def _handle_server_exception(self, request, exc):
        """

        :param request:
        :param exc: web exception whose status is available
        :return:
        """
        # 检查相关处理
        if self.only_process_on_get:
            if request.method == 'GET':
                html = self.error_html.get(exc.status)
                if html:
                    return self._render_template(html, exc.status,
                                                 path=request.path,
                                                 method=request.method)
                else:
                    # default string
                    resp = Response(
                        body=self._DEFAULT_ERROR_STRING.format(method=request.method, path=request.path, reason=exc.reason),
                        status=exc.status)
                    resp.content_type = 'text/html;charset=utf-8'
                    return resp
        # 返回基类的调用
        return super(Jinja2TemplateResponseMiddleware, self)._handle_server_exception(request, exc)

    def _handle_route_exception(self, request, exc):
        """
        handle route call error
        :param request:
        :param exc: BaseException or its derived class' instance
        :return:
        """

        # 检查相关处理
        if self.only_process_on_get:
            if request.method == 'GET':
                if self.route_error_html:
                    return self._render_template(self.route_error_html, 500,  # server internal error
                                                 path=request.path,
                                                 method=request.method)
                else:
                    # default error
                    resp = Response(
                        body=self._DEFAULT_ROUTE_ERROR_STRING.format(method=request.method,
                                                                     path=request.path,
                                                                     error_class=exc.__class__.__name__,
                                                                     traceback=traceback.format_exc()),
                        status=500)

                    resp.content_type = 'text/html;charset=utf-8'
                    return resp
        return super(Jinja2TemplateResponseMiddleware, self)._handle_route_exception(exc=exc, request=request)


def make_middleware_wrap(middleware_obj):
    """
    create middleware. Work around for aiohttp that pass the app parameter to the middleware __call__ method asked request and handler
    :param middleware_obj: Middleware or its derived class
    :return:
    """
    if not isinstance(middleware_obj, Middleware):
        raise ValueError("'middleware_obj' must be an instance of Middleware or its derived class")

    @middleware
    async def work_around_middleware(request, handler):
        return await middleware_obj(request=request, handler=handler)
    return work_around_middleware
