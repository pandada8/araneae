import yaml
import os
from .parser import get_parser
import logging
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
from jinja2 import Template
from csv import DictWriter
import tempfile

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

    def __init__(self, info, core_config={}):
        self.info = info
        self.config = core_config
        print(self.config)
        logger.debug('got info', info)
        self.parser = get_parser(info)
        self.fail = False

    def run(self):
        try:
            self.parser.run()
            self.generate_the_csv()
            self.generate_the_report()
            self.send_report()
        except Exception as e:
            logger.exception(e)
            self.fail = True

    def generate_the_csv(self):

        output = tempfile.NamedTemporaryFile(delete=False, mode="w")
        logger.info('Start generating the csv file: %s', output.name)
        output_fileds = ['title', 'touched', 'id', 'status']
        csv_writer = DictWriter(output, output_fileds, extrasaction="ignore")
        csv_writer.writeheader()
        csv_writer.writerows(sorted(self.parser.result, key=lambda x: (x['status'], x['title'])))
        output.close()
        self.csv_path = output.name


    def generate_the_report(self):

        temp = Template('./mail_template.html')
        pages = {
            "untranslated": [],
            "orphan": [],
            "outdated": [],
            "normal": []
        }
        for i in self.parser.result:
            pages[i['status']].append(i)

        data = {
            "time": datetime.now(),
            "tasks": self.info['name'],
            "pages": sum(i for i in pages.values())
        }
        data.update(pages)
        self.generated = temp.render(data=self.parser.get_result(), **data)
        print(self.generated)
        

    def send_report(self):
        target = self.config['Core']['smtp_email']
