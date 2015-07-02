import logging
from ..error import NoSuchParser

logger = logging.getLogger('parser')
_parser = []
__all__ = ['reg_parser', 'get_parser']

def reg_parser(name):
    def wrapper(cls):
        _parser[name] = cls
        logger.debug('New Parser %s registered', name)
        return cls
    return wrapper

def get_parser(type, info):
    if type in _parser:
        return _parser[type](info)
    else:
        raise NoSuchParser(type)
