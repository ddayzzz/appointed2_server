from ap_logger.logger import set_logger_format
import logging
set_logger_format(level=logging.ERROR)


from ap_http.server import BaseHttpServer
from ap_samples.http_server import handlers
from ap_database.dbmgr import MySQLManager
from ap_http.middlewares import make_auth_middleware, make_data_middleware, ResponseMiddleware, make_response_middleware
from ap_http.signals import make_shutdown_sqlmanager_signal

def main():

    dbm = MySQLManager(username='aitest', password='test123', dbname='aicolor', host='127.0.0.1', port=3306)
    server = BaseHttpServer('SampleServer', '127.0.0.1', 9000)
    server.add_route_group(handlers)
    server.add_template('templates')
    server.add_middleware([make_data_middleware(), make_response_middleware(ResponseMiddleware())])
    server.add_kwargs_to_route(dbm=dbm, sb=250)
    server.add_shutdown_signal(make_shutdown_sqlmanager_signal(dbm))
    server.run_until_shutdown()


if __name__ == '__main__':
    main()
