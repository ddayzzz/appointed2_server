# coding=utf-8
__author__ = 'Shu Wang <wangshu214@live.cn>'
__version__ = '0.0.0.1'
__all__ = ['make_app']
__doc__ = """Appointed2 - define a simple app with mysql connection. It can be run as a gunicron module or 
standalone model"""


def make_app(dbusername, dbpasswd, dbname, dbhost, dbport, log_level='info'):
    """
    this is factory for creating a http app
    :param dbusername:
    :param dbpasswd:
    :param dbname:
    :param dbhost:
    :param dbport:
    :param log_level:
    :return:
    """
    from ap_logger.logger import set_logger_format
    set_logger_format(level=log_level)

    from ap_http.app import BaseHttpApp
    import handlers
    from ap_database.dbmgr import MySQLManager
    from ap_http.middlewares import make_middleware_wrap
    from ap_http.middlewares import Jinja2TemplateResponseMiddleware
    from ap_http.signals import make_shutdown_sqlmanager_signal
    from model import User

    dbm = MySQLManager(username=dbusername, password=dbpasswd, dbname=dbname, host=dbhost, port=dbport)
    server = BaseHttpApp('SampleServer')
    server.add_route_group(handlers)

    server.add_middleware([make_middleware_wrap(Jinja2TemplateResponseMiddleware(templates_dir='./templates'))])
    server.add_kwargs_to_route(dbm=dbm, sb='TOO YOUNG')
    server.add_shutdown_signal(make_shutdown_sqlmanager_signal(dbm))
    return server


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="Sample app with database and user cookie access")
    parser.add_argument('--port', default=9999)
    parser.add_argument('--host', default='localhost')
    parser.add_argument('--dbusername', default='aitest')
    parser.add_argument('--dbpasswd', default='test123')
    parser.add_argument('--dbname', default='aicolor')
    parser.add_argument('--dbhost', default='localhost')
    parser.add_argument('--dbport', default=3306)
    parser.add_argument('--loglevel', default='info')
    # parse argument and instance the app
    args = parser.parse_args()
    app = make_app(dbusername=args.dbusername,
                   dbpasswd=args.dbpasswd,
                   dbhost=args.dbhost,
                   dbport=args.dbport,
                   dbname=args.dbname,
                   log_level=args.loglevel)
    # run on standalone mode
    from ap_deploy.http_deployer import run_on_standalone
    run_on_standalone(app, host=args.host, port=args.port)
