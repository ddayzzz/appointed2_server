# coding=utf-8
__author__ = 'Shu Wang <wangshu214@live.cn>'
__version__ = '0.0.0.1'
__all__ = []
__doc__ = 'Appointed2 - shutdown signals'


def make_shutdown_sqlmanager_signal(sqlmanager):
    """
    close SQL connection pool
    :param sqlmanager: SQLManager's instance
    :return:
    """
    async def on_shutdown(app):
        await sqlmanager.close()
    return on_shutdown
