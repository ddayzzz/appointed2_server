# coding=utf-8

__author__ = 'Shu Wang <wangshu214@live.cn>'
__version__ = '0.0.0.1'
__all__ = []
__doc__ = 'Appointed2 - exceptions for ap_http server'


class CallbackError(BaseException):

    def __init__(self, msg):
        super(CallbackError, self).__init__()
        # message
        self.message = msg
