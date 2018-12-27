# coding=utf-8
__author__ = 'Shu Wang <wangshu214@live.cn>'
__version__ = '0.0.0.1'
__all__ = ['make_logger', 'set_logger_format']
__doc__ = 'Appointed2 - set logger'
import logging
import sys


def set_logger_format(level=logging.INFO, stream=sys.stdout):
    """
    config the logger format and output target
    :param level: the minimum level for output log
    :param stream: stream to output
    :return:
    """
    logging.basicConfig(stream=stream, level=level, format='%(name)s: %(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s', datefmt='%a, %d %b %Y %H:%M:%S')

def make_logger(name):
    """
    get named logger
    :param name: name
    :return: named logger
    """
    return logging.getLogger(name=name)
