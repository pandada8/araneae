import yaml
import os
from .parser import get_parser
import logging
import smtplib
from email.mime.text import MIMEText
from jinja2 import Template

logger = logging.getLogger('tasks')


def parse_tasks(tasks):
    parsed = []
    for i in tasks:
        if not i.startswith("/"):
            i = os.path.join(os.path.split(__file__)[0], 'tasks', i + ".yaml")
        if not os.path.exists(i):
            print("Can't find the {}".format(i))
            continue
        parsed.append(yaml.load(open(i)))
    return parsed


def parse_all_tasks():
    tasks = []
    for i in os.listdir(os.path.join(os.path.split(__file__)[0], 'tasks')):
        if i.endswith('.yaml'):
            tasks.append(os.path.splitext(i)[0])
    return parse_tasks(tasks)


class Task:

    def __init__(self, info):
        self.info = info
        logger.debug('got info', info)
        self.parser = get_parser(info)
        self.fail = False

    def run(self):
        try:
            self.parser.run()
        except Exception as e:
            logger.exception(e)
            self.fail = True

    def generate_the_report(self):
        temp = Template('./mail_template.html')
        return

    def report(self):
        pass