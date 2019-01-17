# coding=utf-8
__author__ = 'Shu Wang <wangshu214@live.cn>'
__version__ = '0.0.0.1'
__all__ = ['run_on_standalone']
__doc__ = """Appointed2 - deployers for different systems(configurations). For unix's deployment, 
using Gunicorn+nginx(offer fast static file access) is 
one of best practices"""


def run_on_standalone(app, host, port, *args, **kwargs):
    """
    run standalone mode in system
    :param app: BaseApp or its derived class instance
    :param host: bind host e.g localhost
    :param port: bind port e.g 9999
    :param args:
    :param kwargs:
    :return:
    """
    from aiohttp.web import run_app
    run_app(app, host=host, port=port, *args, **kwargs)

