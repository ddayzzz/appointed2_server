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

    def add_template(self, path, **kw):
        options = dict(
            autoescape=kw.get('autoescape', True),
            block_start_string=kw.get('block_start_string', '{%'),
            block_end_string=kw.get('block_end_string', '%}'),
            variable_start_string=kw.get('variable_start_string', '{{'),
            variable_end_string=kw.get('variable_end_string', '}}'),
            auto_reload=kw.get('auto_reload', True)
        )
        env = Environment(loader=FileSystemLoader(path), **options)
        filters = kw.get('filters', None)
        if filters is not None:
            for name, f in filters.items():
                env.filters[name] = f
        self.template = env

    def add_route_group(self, name):
        rt = RouteGroup(imported_name=name)
        for obj in rt.route_callbacks:
            self.router.add_route(obj.router.method, obj.router.route, obj)

    def add_middleware(self, middlewares):
        if isinstance(middlewares, Middleware):
            self.middlewares.append(middlewares)
        else:
            self.middlewares.extend(middlewares)  # iterable

    def add_template_filter(self, name, callback):
        if self.template:
            self.template.filters[name] = callback

    def add_shutdown_signal(self, signal_callback):
        self.on_shutdown.append(signal_callback)

    def add_kwargs_to_route(self, **kwargs):
        self.ap_kwargs.update(kwargs)
