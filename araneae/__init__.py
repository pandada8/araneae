""" Spider

Usage:
    araneae task list [-v | -vv | -vvv]
    araneae task run [-v | -vv | -vvv] <tasks>...

Options:
    -v -vv -vvv   Verbose Mode

"""
from docopt import docopt
from . import tasks
import os
import yaml
import logging
# from araneae import Araneae

logger = logging.getLogger('core')

def loadConfig():
    config = {}
    for i in ['config.yaml']:
        if os.path.exist(i):
            config.update(yaml.load(open(i))) # FIXME: add shadow update
            logger.debug('Config updated with config file %s', os.path.abspath(i))
    return config

def print_tasks(tasks):
    for i in tasks:
        f = "{name}\n" \
            "  Type: {type}\n" \
            "  Source: {url}\n" \
            "  Target Language: {lang}\n"
        print(f.format(**i))

def main():
    argument = docopt(__doc__, version="araneae 0.1")
    print(argument)
    if argument['task']:
        if argument['run']:
            if not argument['<tasks>']:
                todo_tasks = tasks.parse_all_tasks()
            else:
                todo_tasks = tasks.parse_tasks(argument['<tasks>'])
            araneae = Araneae(todo_tasks)  #TODO: rewrite whole app with Araneae class
            araneae.run()
            raise SystemExit
        elif argument['list']:
            all_tasks = tasks.parse_all_tasks()
            print_tasks(all_tasks)
            raise SystemExit
    elif argument['help']:
        print(__doc__)
        raise SystemExit
