import yaml
import os
from .parser import get_parser

def parse_tasks(tasks):
    parsed = []
    for i in tasks:
        parsed.append(yaml.load(os.path.join('tasks', i + '.yaml')))
    return parsed

def parse_all_tasks():
    tasks = []
    for i in os.listdirs('tasks'):
        if i.endswith('.yaml'):
            tasks.append(os.path.splitext(i)[0])
    return parse_tasks(tasks)

class Task:
    def __init__(self, info):
        self.info = info
        self.parser = get_parser(info)
    def run(self):
        try:
            self.parser.run()
        except:
            pass

    def report(self):
        pass
