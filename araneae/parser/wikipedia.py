import requests
from araneae.parser import reg_parser, ParserBase


@reg_parser("wikipedia")
class WikipediaParser(ParserBase):

    def __init__(self):
        pass

    def get_all_post(self):
        pass

    def get_info(self):
        pass

    def _bot_login(self, username, password):
        pass
