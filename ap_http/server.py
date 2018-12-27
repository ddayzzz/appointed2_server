# coding=utf-8

__author__ = 'Shu Wang <wangshu214@live.cn>'
__version__ = '0.0.0.1'
__all__ = ['BaseHttpServer']
__doc__ = 'Appointed2 - simple server definition'
from aiohttp.web import Application, run_app
from jinja2 import FileSystemLoader, Environment
from ap_http.route import RouteGroup
from ap_logger import logger


class BaseHttpServer(object):
    """
    BaseHttpServer : basic http server
    """

    def __init__(self, name, host, port):
        '''
        :param name: server name
        :param host: host
        :param port: port
        '''
        self._app = Application(logger=logger.make_logger('CORE'))  # maybe can specify logger?
        self._app.ap_kwargs = dict()  # args passed to route
        self._app.template = None
        self.name = name
        self.host = host
        self.port = port

    def run_until_shutdown(self):
        """
        run ap_http server until control-c is pressed and call the shutdown_signal
        :return:
        """
        run_app(self._app, host=self.host, port=self.port)

    def add_static(self, prefix, path, *args, **kwargs):
        self._app.router.add_static(prefix=prefix, path=path)

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
        self._app.template = env

    def add_route_group(self, name):
        rt = RouteGroup(imported_name=name)
        for obj in rt.route_callbacks:
            self._app.router.add_route(obj.router.method, obj.router.route, obj)

    def add_middleware(self, middlewares):
        self._app.middlewares.extend(middlewares)

    def add_template_filter(self, name, callback):
        if self._app.template:
            self._app.template.filters[name] = callback

    def add_shutdown_signal(self, signal_callback):
        self._app.on_shutdown.append(signal_callback)

    def add_kwargs_to_route(self, **kwargs):
        self._app.ap_kwargs.update(kwargs)
