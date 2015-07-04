import requests
from araneae.parser import reg_parser, ParserBase
import logging
import time

logger = logging.getLogger('parser.wikipedia')


@reg_parser("wikipedia")
class WikipediaParser(ParserBase):

    def __init__(self, config):
        self.r = requests.session()
        self.config = config

    def _api_call(self, method, param, **kwargs):
        param['format'] = 'json'
        param['maxlag'] = '5'

        response = self.r.request(method, self.config['url'], params=param, **kwargs)
        if 'Retry-After' in response.headers and response.headers['Content-Type'] == 'text/plain':
            delay = int(response.headers['Retry-After'])
            logger.warn('Lag detected, we will wait for %d seconds', delay)
            time.sleep(delay)
            logger.debug('wake up again')
        print(response.url)
        return response.json()

    def get_all_post(self):
        pass

    def get_info(self):
        param = {
            "action": "query",
            "meta": "siteinfo",
            "siprop": "general|namespaces|statistics"
        }
        data = self._api_call('GET', param)
        print(data)

    def run(self):
        self.get_info()

    def _bot_login(self, username, password):
        pass
