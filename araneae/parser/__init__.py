import logging
from ..error import NoSuchParser

logger = logging.getLogger('parser')
_parser = {}
__all__ = ['reg_parser', 'get_parser']

def reg_parser(name):
    def wrapper(cls):
        _parser[name] = cls
        logger.debug('New Parser %s registered', name)
        return cls
    return wrapper

def get_parser(info):
    if info['type'] in _parser:
        return _parser[info['type']](info)
    else:
        raise NoSuchParser(info['type'])

class ParserBase(object):

    def __init__(self):
        pass

    def run(self):
        pass

    def report(self):
        pass

from . import wikipedia
