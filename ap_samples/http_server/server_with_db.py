# coding=utf-8
__author__ = 'Shu Wang <wangshu214@live.cn>'
__version__ = '0.0.0.1'
__all__ = ['SampleApp']
__doc__ = """Appointed2 - define a simple app with mysql connection. It can be run as a gunicron module or 
standalone model"""
from ap_http.app import BaseHttpApp
from ap_samples.http_server import handlers
from ap_database.dbmgr import MySQLManager
from ap_http.middlewares import make_auth_middleware, make_data_middleware, make_response_middleware
from ap_http.middlewares import ResponseMiddleware, UserAuthMiddleware
from ap_http.signals import make_shutdown_sqlmanager_signal
from ap_samples.http_server.model import User


def _make_app(dbusername, dbpasswd, dbname, dbhost, dbport):
    """
    protected function to make a simple application and connect to mysql
    :param dbusername:
    :param dbpasswd:
    :param dbname:
    :param dbhost:
    :param dbport:
    :return:
    """
    dbm = MySQLManager(username=dbusername, password=dbpasswd, dbname=dbname, host=dbhost, port=dbport)
    server = BaseHttpApp('SampleServer')
    server.add_route_group(handlers)
    server.add_template('templates')
    server.add_middleware([make_data_middleware(),
                           make_auth_middleware(
                               UserAuthMiddleware(cookie_name="ap", cookie_key="haha", type_of_user=User, dbmgr=dbm)),
                           make_response_middleware(ResponseMiddleware())])
    server.add_kwargs_to_route(dbm=dbm, sb=250)
    server.add_shutdown_signal(make_shutdown_sqlmanager_signal(dbm))
    return server


async def SampleApp(dbusername, dbpasswd, dbname, dbhost, dbport):
    return _make_app(dbusername, dbpasswd, dbname, dbhost, dbport)


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
    # parse argument and instance the app
    args = parser.parse_args()
    app = _make_app(dbusername=args.dbusername,
                    dbpasswd=args.dbpasswd,
                    dbhost=args.dbhost,
                    dbport=args.dbport,
                    dbname=args.dbname)
    # run on standalone mode
    from ap_deploy.http_deployer import run_on_standalone
    run_on_standalone(app, host=args.host, port=args.port)
