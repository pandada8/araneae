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

logger = logging.getLogger('core')
# disable the requests log
requests_logger = logging.getLogger('requests.packages.urllib3.connectionpool')
requests_logger.setLevel(60)


def loadConfig():
    config = {}
    for i in [os.path.join(os.path.split(__file__)[0], 'config.yaml')]:
        if os.path.exists(i):
            config.update(yaml.load(open(i)))  # FIXME: add shadow update
            logger.debug('Config updated with config file %s', os.path.abspath(i))
    return config

config = {}


def print_tasks(tasks):
    for i in tasks:
        f = "{name}\n" \
            "  Type: {type}\n" \
            "  Source: {url}\n" \
            "  Target Language: {lang}\n"
        print(f.format(**i))


def run_tasks(todo_tasks):
    global config
    for i in todo_tasks:
        logger.info('Starting task %s', i['name'])
        t = tasks.Task(i, core_config=config)
        t.run()


def main():
    config.update(loadConfig())
    argument = docopt(__doc__)
    if argument['-v']:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    logging.info('Welcome to araneae, a python-powered wiki robot!')
    # set basic screen logging stuff
    # print(argument)
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
