"""
Araneae
A Wiki bot for translations

Usage:
    araneae list [-v | --verbose]
    araneae run [-v | --verbose] [TASKS ...]
    araneae run [-v | --verbose]
"""
from docopt import docopt
from . import tasks
import os
import yaml
import logging
# from araneae import Araneae

logger = logging.getLogger('core')
# disable the requests log
requests_logger = logging.getLogger('requests.packages.urllib3.connectionpool')
requests_logger.setLevel(60)


def loadConfig():
    config = {}
    for i in ['config.yaml']:
        if os.path.exist(i):
            config.update(yaml.load(open(i)))  # FIXME: add shadow update
            logger.debug('Config updated with config file %s', os.path.abspath(i))
    return config


def print_tasks(tasks):
    for i in tasks:
        f = "{name}\n" \
            "  Type: {type}\n" \
            "  Source: {url}\n" \
            "  Target Language: {lang}\n"
        print(f.format(**i))


def run_tasks(todo_tasks):
    for i in todo_tasks:
        logger.info('Starting task %s', i['name'])
        t = tasks.Task(i)
        t.run()


def main():
    argument = docopt(__doc__)
    if argument['-v']:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    logging.info('Welcome to araneae, a python-powered wiki robot!')
    # set basic screen logging stuff
    print(argument)
    if argument['run']:
        if not argument['TASKS']:
            todo_tasks = tasks.parse_all_tasks()
        else:
            todo_tasks = tasks.parse_tasks(argument['TASKS'])
        run_tasks(todo_tasks)
        raise SystemExit
    elif argument['list']:
        all_tasks = tasks.parse_all_tasks()
        print_tasks(all_tasks)
        raise SystemExit
    else:
        print(__doc__)
        raise SystemExit
