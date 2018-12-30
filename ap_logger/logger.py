# coding=utf-8
__author__ = 'Shu Wang <wangshu214@live.cn>'
__version__ = '0.0.0.1'
__all__ = ['make_logger', 'set_logger_format']
__doc__ = 'Appointed2 - set logger'
import logging
import sys

__logging_const_mapping = {
    'info': logging.INFO,
    'error': logging.ERROR,
    'debug': logging.DEBUG,
    'warning': logging.WARNING
}


def set_logger_format(level='info', stream=sys.stderr):
    """
    config the logger format and output target
    :param level: the minimum level for output log. info, debug, error, warning
    :param stream: stream to output
    :return:
    """

    logging.basicConfig(stream=stream,
                        level=__logging_const_mapping.get(level, logging.INFO),
                        format='[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s')


def make_logger(name):
    """
    get named logger
    :param name: name
    :return: named logger
    """
    return logging.getLogger(name=name)
