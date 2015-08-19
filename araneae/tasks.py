import yaml
import os
from .parser import get_parser
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
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
        # we first sort by the status then sort by the title
        output.close()
        self.csv_path = output.name

    def generate_the_report(self):

        self.generated = datetime.now()
        template_html = os.path.join(os.path.split(__file__)[0], 'mail_template.html')
        template_txt = os.path.join(os.path.split(__file__)[0], 'mail_template.txt')
        html = Template(open(template_html).read())
        txt = tempfile(open(template_txt).read())
        pages = {
            "untranslated": [],
            "orphan": [],
            "outdated": [],
            "normal": []
        }
        for i in self.parser.result:
            pages[i['status']].append(i)
        for i in pages:
            pages[i] = sorted(pages[i], key=lambda x: (x['title'], x['touched']))
        data = {
            "time": self.generated,
            "tasks": self.info['name'],
            "pages": sum(len(i) for i in pages.values()),
            "translated": len(pages['normal']) + len(pages['orphan']),
            "todo": len(pages['untranslated']) + len(pages['outdated']),
            'data': pages
        }
        data['data'].pop('normal')
        self.generated_html = html.render(**data)
        self.generated_txt = txt.render(**data)

        logger.info('Finished generate the txt and html report')

    def send_report(self):

        sender = self.config['Core']['smtp_email']
        reciver = self.info['report']

        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'Araneae Result ({})'.format(self.generated)
        msg['From'] = sender
        msg['To'] = reciver
        part1 = MIMEText(self.generated_txt, "plain")
        part2 = MIMEText(self.generated_html, 'html')
        msg.attach(part1)
        msg.attach(part2)

        server, port = self.config['Core']['smtp_server'].split(':')
        mail = smtplib.SMTP(server, port)

        mail.ehlo()

        mail.starttls()
        mail.login(sender, self.config['Core']['smtp_password'])
        mail.send(sender, reciver, msg.as_string())
        mail.quit()
