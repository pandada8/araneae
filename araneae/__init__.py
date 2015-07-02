""" Spider

Usage:
    araneae task list [-v | -vv | -vvv]
    araneae task run [-v | -vv | -vvv] <tasks>...

Options:
    -v -vv -vvv   Verbose Mode

"""
from docopt import docopt
from araneae import tasks
# from araneae import Araneae
def main():
    argument = docopt(__doc__, version="araneae 0.1")
    print(argument)
    if argument['task']:
        if argument['run']:
            if not argument['<tasks>']:
                todo_tasks = tasks.parse_all_tasks()
            else:
                todo_tasks = tasks.parse_tasks(argument['<tasks>'])
            araneae = Araneae(todo_tasks)
            araneae.run()
            raise SystemExit
        elif argument['list']:
            tasks.parse_all_tasks()
            raise SystemExit
    elif argument['help']:
        print(__doc__)
        raise SystemExit
