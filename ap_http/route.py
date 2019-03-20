# coding=utf-8
import functools
import inspect
import asyncio
from urllib import parse

from ap_http.exceptions import CallbackError
from ap_logger.logger import make_logger

__author__ = 'Shu Wang <wangshu214@live.cn>'
__version__ = '0.0.0.1'
__all__ = ['Router', "get", "post"]
__doc__ = 'Appointed2 - lower level methods and classes for async ap_http server and define the decorators for post and get method and router callback object'


_logger = make_logger('INITROUTE')


def get(path, **kwargs):
    """
    get method decorator
    :param path: route
    :param kwargs:
    :return:
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kw):
            return func(*args, **kw)
        wrapper.__method__ = 'GET'
        wrapper.__route__ = path
        return wrapper
    return decorator


def post(path, **kwargs):
    """
    Post method
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kw):
            return func(*args, **kw)
        wrapper.__method__ = 'POST'
        wrapper.__route__ = path
        return wrapper
    return decorator


class Router(object):

    def __init__(self, method, route, func, doc=None):
        """
        Router ctor
        :param method: method for ap_http
        :param route: method's path
        :param doc: document of method
        :param func: callback function
        """
        self.method = method
        self.route = route
        self.doc = doc
        self.func = func  # 关联的函数

    def __repr__(self):
        return '<Router {method} : {route}>'.format(method=self.method, route=self.route)


class RouterCallBack(object):

    def __init__(self, routerObj):
        """
        RouterCallBack ctor
        :param routerObj: instance of Router
        """
        if not isinstance(routerObj, Router):
            raise ValueError("routerObj is not instance of Router")
        self.router = routerObj

    async def __call__(self, request):
        """
        Call the inner function of every route
        :param request: request object
        :return: any response format
        """
        # get app
        app = request.app
        # 获取函数的参数表
        required_args = inspect.signature(self.router.func).parameters
        # logger.get_logger().info('需要的参数: %s' % required_args)
        # 获取从GET或POST传进来的参数值，如果函数参数表有这参数名就加入
        kw = dict()
        if request.method == 'POST':
            # convert the post form to json object which preprocessed and placed in request object's field named __data__
            if getattr(request, '__data__', None):
                kw = {arg: value for arg, value in request.__data__.items() if
                      arg in required_args}  # POST需要进行参数的一些转换，这个转换在data工厂中。数据存储在__data__属性中
            # else:
            #     kw = dict()  # 只有传递了数据才会有__data__
        # 参数转换
        # GET/POST 参数有可能需要类似于http://xxx.com/blog?id=5&name=ff之类的参数
        qs = request.query_string
        if qs:
            # logger.get_logger().info('GET指令的query参数: %s' % request.query_string)
            kw.update({arg: value if isinstance(value, list) and len(value) > 1 else value[0] for arg, value in parse.parse_qs(qs, True).items()})# 保留空格。将查询参数添加到kw已知的参数列表 ref https://raw.githubusercontent.com/icemilk00/Python_L_Webapp/master/www/coroweb.py。可以支持传递数组
        else:
            kw.update({arg: value for arg, value in request.match_info.items() if arg in required_args})
        # 获取match_info的参数值，例如@get('/blog/{id}')之类的参数值
        kw.update(request.match_info)
        # 添加其他的 关键字
        if 'request' in required_args:
            kw['request'] = request
        # fill the kwargs
        for k, v in app.ap_kwargs.items():
            if k in required_args:
                kw[k] = v
        # 检查参数表中有没参数缺失
        for key, arg in required_args.items():
            # request参数不能为可变长参数
            if key == 'request' and arg.kind in (arg.VAR_POSITIONAL, arg.VAR_KEYWORD):
                return CallbackError(msg="'request' must be immutable parameter")
            # 如果参数类型不是变长列表和变长字典，变长参数是可缺省的
            if arg.kind not in (arg.VAR_POSITIONAL, arg.VAR_KEYWORD):
                # 如果还是没有默认值，而且还没有传值的话就报错
                if arg.default == arg.empty and arg.name not in kw:
                    raise CallbackError('missing real parameter: %s' % arg.name)
        return await self.router.func(**kw)  # call the async function


class RouteGroup(object):

    def __init__(self, imported_name):
        """
        RouteGroup ctor. This will search all the functions in specific package and add it into ap_http server object
        :param imported_name: the handler's model name in context. e.g. MyApp.UserHandler
        """
        routes_callbacks = []
        # load package from context
        modObj = imported_name
        # 读取doc、version、author以及各个路由器的信息（只在公共接口中__all__）以及路由的命令行格式（如果有）
        # 合法的模块
        for api in getattr(modObj, '__all__', []):
            fn = getattr(modObj, api)
            if callable(fn):
                # 是一个可调用对象
                method = getattr(fn, '__method__', None)
                path = getattr(fn, '__route__', None)
                if method and path:
                    if not asyncio.iscoroutinefunction(fn) and not inspect.isgeneratorfunction(fn):  # 检查是否是异步函数
                        fn = asyncio.coroutine(fn)
                    # convert into object
                    rt = Router(method=method, route=path, func=fn)
                    #
                    _logger.info('Add route : {rt} -> {fcn}'.format(rt=rt, fcn=fn))
                    routes_callbacks.append(RouterCallBack(rt))
        self.route_callbacks = routes_callbacks
