# coding=utf-8

__author__ = 'Shu Wang <wangshu214@live.cn>'
__version__ = '0.0.0.1'
__all__ = ['BaseHttpApp']
__doc__ = 'Appointed2 - simple server definition'
from aiohttp.web import Application
from jinja2 import FileSystemLoader, Environment
from ap_http.route import RouteGroup
from ap_logger.logger import make_logger
from ap_http.middlewares import Middleware


class BaseHttpApp(Application):
    """
    BaseHttpServer : basic http server
    """

    def __init__(self, name, logger=None, *args, **kwargs):
        '''
        Create http application
        :param name:
        :param logger: define aiohttp.access logger
        :param args:
        :param kwargs:
        '''
        self.ap_kwargs = dict()  # args passed to route
        self.template = None
        self.name = name
        if not logger:
            logger = make_logger('CORE')
        super(BaseHttpApp, self).__init__(logger=logger, *args, **kwargs)

    def add_static(self, prefix, path, *args, **kwargs):
        self.router.add_static(prefix=prefix, path=path)


    def add_route_group(self, name):
        rt = RouteGroup(imported_name=name)
        for obj in rt.route_callbacks:
            self.router.add_route(obj.router.method, obj.router.route, obj)

    def add_middleware(self, middlewares):
        if isinstance(middlewares, Middleware):
            self.middlewares.append(middlewares)
        else:
            self.middlewares.extend(middlewares)  # iterable

    def add_shutdown_signal(self, signal_callback):
        self.on_shutdown.append(signal_callback)

    def add_kwargs_to_route(self, **kwargs):
        self.ap_kwargs.update(kwargs)
