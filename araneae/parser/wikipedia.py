import requests
from araneae.parser import reg_parser, ParserBase
import logging
import time
import re
from http.cookiejar import MozillaCookieJar
import os
from dateutil.parser import parse

logger = logging.getLogger('parser.wikipedia')


@reg_parser("wikipedia")
class WikipediaParser(ParserBase):

    """
    This parser use a small part of the mediawiki api to get the max compatibility.
    """

    def __init__(self, config):
        self.r = requests.session()

        # deal with the session
        folder = os.path.expanduser('~/.cache/araneae/session')
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, config['name'] + '.txt')
        self.r.cookies = MozillaCookieJar(path)

        if os.path.exists(path):
            self.r.cookies.load()

        self.config = config

        self.r.headers["User-Agent"] = "Araneae wiki bot/ (pandada8@gmail.com)"
        self.user_rights = []
        self.logined = False

        # check if we have a robot account
        if self.config.get('username') and self.config.get('password'):
            self.auth = (self.config['username'], self.config['password'])
            logger.debug('load wiki account')
        else:
            self.auth = None

    def login(self):
        if self.auth:
            params = {
                'action': "login",
                'lgname': self.auth[0],
                'lgpassword': self.auth[1]
            }
            data = self._api_call('POST', params)
            if data['login']['result'] == 'Success':
                # ok we logined
                self.logined = True
                self.r.session.save()
                return
            elif data['login']['result'] == 'NeedToken':
                params['lgtoken'] = data['login']['token']
                data = self._api_call('POST', params)
                if data['login']['result'] == 'Success':
                    # ok
                    self.logined = True
                    self.r.session.save()
                    return
                else:
                    # so the login is failed
                    self.logined = False
                    logger.error("Login %s error: %s", self.auth[0], data['login']['result'])
                    return
            else:
                self.logined = False
                logger.error("Login %s error: %s", self.auth[0], data['login']['result'])
                return
        else:
            self.logined = False
            return

    def query_user_rights(self):
        """
        check if the account "is" a bot
        """
        if self.logined:
            params = {
                'action': 'query',
                'meta': "userinfo",
                'uiprop': "rights"
            }
            self.user_rights = self._api_call("GET", params)['query']['userinfo']['rights']
            logger.info('Query <%s> success, rights: %s', self.auth[0], "|".join(self.user_rights))
        else:
            logger.info('Not logined ignore the checking')

    @property
    def _limit(self):
        if 'apihighlimits' in self.user_rights:
            return 5000
        else:
            return 500

    def _api_call(self, method, param, **kwargs):
        param['format'] = 'json'
        param['maxlag'] = '5'
        response = self.r.request(method, self.config['url'], params=param, **kwargs)
        if 'Retry-After' in response.headers and response.headers['Content-Type'] == 'text/plain':
            delay = int(response.headers['Retry-After'])
            logger.warn('Lag detected, we will wait for %d seconds', delay)
            time.sleep(delay)
            logger.debug('wake up again')
        data = response.json()
        return data

    def get_all_post(self):
        continue_from = ""
        fetched = []
        while True:
            params = {
                "gapcontinue": continue_from,
                "gapnamespace": self.target_namespace,  # Only search the main namespace
                "gapfilterredir": "nonredirects",  # we don't care the redirect page
                "gaplimit": self._limit,
                'action': 'query',
                "generator": 'allpages',
                "lllimit": 500,
                "llprop": "url",
                "prop": 'info|templates|langlinks',
            }
            data = self._api_call('GET', params)
            for i in data['query']['pages'].values():
                logger.debug('page %s : "%s", rv: %s, contentmodel: %s', i['pageid'], i['title'], i['lastrevid'], i['contentmodel'])
                fetched.append(i)

            logger.info('%d pages fetched', len(fetched))

            if 'query-continue' in data and 'allpages' in data['query-continue']:
                continue_from = data['query-continue']['allpages']['gapcontinue']
            else:
                break

        with open('2.json', 'w') as fp:
            import json
            json.dump(fetched, fp)
        logger.info('Fetching finished, fetch %d pages in all', len(fetched))
        return fetched

    def find_the_result(self, all_posts):

        def generate_info(zh_cn=None, en=None):
            if zh_cn is None and en is None:
                raise TypeError("The zh_cn and en cannot be both none")
            if zh_cn is None:
                page = en
                page['status'] = 'untranslated'
            elif en is None:
                page = zh_cn
                page['status'] = "orphan"
            else:
                page = zh_cn
                if parse(zh_cn['touched']) < parse(en['touched']):
                    page['status'] = 'outdated'
                else:
                    page['status'] = 'normal'
            return page

        def comparre_time(iso1, iso2):
            """
            compare two iso format time, the timezone is dropped
            """
            return parse(iso1) < parse(iso2)

        pages = {}
        # non_english = re.compile(r'\(([^\x00-\x7F]+?)\)')
        non_english = re.compile(r'\((\w+?)\)')
        important = ['Out of date', 'Translateme']
        # prepare: flat the data and add langs

        # the question is in the archlinux wiki, all page's `pagelanguage` is 'en', and we can't also judge
        # the name by langlinks, since many of them are the same
        # so the langlinks only used to show the languages this paged translated into
        # and not used in judging which the page used.
        for i in all_posts:
            lang = non_english.search(i['title'])

            i['langs'] = dict((j['lang'], j['url']) for j in i.get('langlinks', []))  # the langlinks may be empty
            i['templates'] = [j['title'].replace('Template:', '') for j in i.get('templates', [])]
            # i['templates'] = [j for j in i.get('templates', []) if i in important] # TODO: Check the corrent name of the translateme

            # should we remove the original links?
            # i.remove('langlinks')

            # store the data in a dict
            if lang:
                i['lang'] = lang.group().strip('()')
                original_title = i['title'].replace(lang.group(), "").strip()

                if pages.get(original_title):
                    pages[original_title][i['lang']] = i
                else:
                    pages[original_title] = {
                        i['lang']: i
                    }
            else:
                i['lang'] = 'en'
                pages[i['title'].strip()] = {
                    '*': i
                }

        result = []

        def find_zh_CN(pages):
            if pages.get('zh-cn'):
                return pages['zh-cn']
            for i, j in pages.items():
                if '简体中文' in j['title']:
                    return j

        def find_en(pages):
            if pages.get('en'):
                return pages['en']
            else:
                return list(pages.values())[0]

        for title, passages in pages.items():
            logger.debug('Deal with %s', title)

            zh_cn = find_zh_CN(passages)
            en = find_en(passages)
            # print(zh_cn, en, pages)
            try:
                page = generate_info(zh_cn=zh_cn, en=en)
            except TypeError:
                raise  # todo: deal with the error
            result.append(page)

        return result

    def find_main_namespace(self):
        param = {
            "action": "query",
            "meta": "siteinfo",
            "siprop": "general|namespaces|statistics"
        }
        data = self._api_call('GET', param)
        self.page_number = data['query']['statistics']['pages']
        self.article_number = data['query']['statistics']['articles']
        logger.info('Got info:' '\tPages:\t%d' '\tArticles:\t%d', self.page_number, self.article_number)
        for i in data['query']['namespaces'].values():
            if i['*'] == "":
                # we got the main namespace
                self.target_namespace = i['id']
                logger.info('Using %s as the main namespace id', i["id"])
                break
        else:
            logger.warn('fail to find the main namespace, use the 0 as the main namespace id')
            self.target_namespace = 0

    def run(self):
        try:
            self.login()
            self.query_user_rights()
            self.find_main_namespace()
            all_post = self.get_all_post()
            self.result = self.find_the_result(all_post)

        except Exception as e:
            logger.exception(e)
            logger.error('unexcepted expcetion occured')

    def get_result(self):
        return self.result