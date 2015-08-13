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

            logger.info(' pages fetched', len(fetched))

            if 'query-continue' in data:
                continue_from = data['query-continue']['allpages']['gapcontinue']
            else:
                break

        logger.info('Fetching finished, fetch %d pages in all', len(fetched))
        return fetched

    def find_the_untranslated(self, all_posts):

        def comparre_time(iso1, iso2):
            """
            compare two iso format time, the timezone is dropped
            """
            return parse(iso1) < parse(iso2)

        pages = {}
        non_english = re.compile(r'\(([^\x00-\x7F]+?)\)')
        important = ['Out of date', 'Translateme']
        # prepare: flat the data and add langs

        # the question is in the archlinux wiki, all page's `pagelanguage` is 'en', and we can't also judge
        # the name by langlinks, since many of them are the same
        # so the langlinks only used to show the languages this paged translated into
        # and not used in judging which the page used.
        for i in all_posts:
            lang = non_english.search(i['title'])
            i['lang'] = lang.strip('()')
            i['langs'] = dict((j['lang'], j['url']) for j in i.get('langlinks', []))  # the langlinks may be empty
            i['templates'] = [j for j in i.get('templates', [])]
            # i['templates'] = [j for j in i.get('templates', []) if i in important] # TODO: Check the corrent name of the translateme

            # should we remove the original links?
            # i.remove('langlinks')

            # store the data in a dict
            if i['lang']:
                original_title = i['title'].replace(lang, "")

                if pages.get(original_title):
                    pages[original_title][i['lang']] = i
                else:
                    pages[original_title] = {
                        i['lang']: i
                    }
            else:
                pages[i['title']] = {
                    '*': i
                }

        result = []

        for i, j in pages.items():
            logger.debug('Deal with %s', i)
            if len(j) == 1:
                (lang, page), = j.items()
                if re.search('[\x00-\x7F]+', page['title']).group() == page['title']:
                    # pure ascii, should be a english page
                    page['status'] = 'untranslated'
                else:
                    page['status'] = 'ignore'
                result.append(page)
            else:
                langs = set(sum(i['langs'] for i in j.values()))
                if not langs:
                    # untranslated
                    page = j.values[0]
                    page['status'] = 'untranslated'
                    result.append(page)
                    continue

                if 'zh-cn' in langs:
                    # let's find out which page we have is in chinese
                    if '简体中文' in j.keys():
                        page = j['简体中文']
                        if "*" in j.keys():
                            # good, simple question
                            en_page = j['*']
                            if comparre_time(page['touched'], en_page['touched']):
                                page['status'] = 'outdated'
                            else:
                                page['status'] = 'normal'
                        else:
                            # but we have no english version
                            page['status'] = 'Orphan'
                    else:
                        # IMPORTANT!!!!
                        # we can't find a chinese version, consider untranslated

                        # try to find a english version
                        link = (langs.get('en') or langs[0])['link']
                        page = j.values()[0]
                        page['status'] = 'untranslated'
                        page['other'] = 'no chinese version found but have zh-cn link'
                        logger.warn('Cannot find chinese version of %s: %s ', page['title'], link)
                elif '简体中文' in j.keys():
                    page = j['简体中文']
                    page['other'] = 'no langlink'
                    logger.warn("Cannot find langlink of %s", page['title'])
                    if "*" in j.keys():
                        # not so complicated
                        en_page = j['*']
                        if comparre_time(page['touched'], en_page['touched']):
                            page['status'] = 'outdated'
                        else:
                            page['status'] = 'normal'
                    else:
                        # again we have no english version
                        page['other'] += ", no english version(maybe wrong title?)"
                        page['status'] += 'Orphan'
                        logger.warn('Cannot find english version of %s: %s ', page[''], link)
                else:
                    if "*" in j.keys():
                        page = j['*']
                    else:
                        page = j.values()[0]
                    page['status'] = 'untranslated'

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
            import json
            with open('1.json') as fp:
                json.dump(self.result, fp)
        except Exception as e:
            logger.exception(e)
            logger.error('unexcepted expcetion occured')
