import requests
from araneae.parser import reg_parser, ParserBase
import logging
import time
from araneae.cache import cache
import re

logger = logging.getLogger('parser.wikipedia')


@reg_parser("wikipedia")
class WikipediaParser(ParserBase):

    def __init__(self, config):
        self.r = requests.session()
        self.config = config
        self.bot = False

    def _api_call(self, method, param, **kwargs):
        param['format'] = 'json'
        param['maxlag'] = '5'
        kwargs.update({'headers': {"User-Agent": "araneae wiki bot/0.1 (pandada8@gmail.com)"}})
        response = self.r.request(method, self.config['url'], params=param, **kwargs)
        if 'Retry-After' in response.headers and response.headers['Content-Type'] == 'text/plain':
            delay = int(response.headers['Retry-After'])
            logger.warn('Lag detected, we will wait for %d seconds', delay)
            time.sleep(delay)
            logger.debug('wake up again')
        data = response.json()
        return data

    def get_all_post(self):
        # TODO: use a memory based database and save the result into the disk after finish
        continue_from = ""
        fetched_numbers = 0
        while True:
            params = {
                "gapcontinue": continue_from,
                "gapnamespace": self.target_namespaces,
                "gapfilterredir": "nonredirects", # we don't care the redirect page
                "gaplimit": 5000 if self.bot else 500,  # fetch as much as we Can
                'action': 'query',
                "generator": 'allpages',
                "prop": 'info',
                "rawcontinue": ""
            }
            data = self._api_call('GET', params)
            for i in data['query']['pages'].values():
                logger.debug('page %s : "%s", rv: %s, contentmodel: %s', i['pageid'], i['title'], i['lastrevid'], i['contentmodel'])
                cache.set(self.config['name'], i)

            fetched_numbers += len(data['query']['pages'])
            logger.info('%d pages fetched', fetched_numbers)

            if 'query-continue' in data:
                continue_from = data['query-continue']['allpages']['gapcontinue']
            else:
                break
        logger.info('Fetching finished, fetch %d pages in all')

    def find_the_untranslated(self):
        translated = []
        original = []
        untranslated = []
        for i in cache.iter_task(self.config['name']):
            if '(' in i['title'] or ')' in i['title'] or re.search(r'[^\x00-\x7F]', i['title']):
                translated.append(i)
            else:
                original.append(i)
        for i in original:
            for j in translated:
                if j['title'].startswith(i['title']) and j['title'] != i['title']:
                    translated_language = j['title'].replace(i['title'], '').strip()[1:-1]
                    if translated_language == '简体中文':
                        logger.debug('Found a %s version for %s, %s', translated_language, i['title'], j['title'])
                        break
            else:
                logger.debug('No translated_version for %s', i['title'])
                untranslated.append(i)
        print(len(untranslated))


    def get_info(self):
        logging.info('get information of the %s', self.config['name'])
        param = {
            "action": "query",
            "meta": "siteinfo",
            "siprop": "general|namespaces|statistics"
        }
        data = self._api_call('GET', param)
        self.page_number = data['query']['statistics']['pages']
        self.article_number = data['query']['statistics']['articles']
        logger.info('Got info:\n' '\tPages:\t%d' '\tArticles:\t%d', self.page_number, self.article_number)
        for i in data['query']['namespaces'].values():
            if i['*'] == "":
                # we got the main namespace
                self.target_namespaces = i['id']
                return


    def run(self):
        try:
            # self.get_info()
            # self.get_all_post()
            self.find_the_untranslated()
        except Exception as e:
            logger.exception(e)
            logger.error('unexcepted expcetion occured')



    def _bot_login(self, username, password):
        raise NotImplemented
        self.bot = True
