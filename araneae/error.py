
class AraneaeError(Exception):
    pass

class NoSuchParser(AraneaeError):

    def __init__(self, parser):
        self.parser = parser

    def __str__(self):
        return "Can't find a parser called {}".format(self.parser)
