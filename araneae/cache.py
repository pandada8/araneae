import sqlite3
import json
import os

class Cache(object):

    def __init__(self):
        self._db = self._init_db()

    def _init_db(self):
        # db_path = os.path.normpath(os.path.join(os.path.split(__file__)[0], '../test.db'))
        db_path = ':memory:'
        conn = sqlite3.connect(db_path, check_same_thread=False, isolation_level=None) # TODO: config this cache path # TODO, avoid usage of empty isolation_level
        # try to check if we have the table
        if not conn.execute('SELECT NAME FROM sqlite_master WHERE type = "table" AND name = ?', ('cache',)).fetchone():
            # create the table we need
            conn.execute('CREATE TABLE cache (page_id TEXT PRIMARY KEY, task TEXT, name TEXT, info TEXT)')
            # the data stuct may changed frequently so just store the json data here
        return conn

    def get(self, task, name):
        result = self._db.execute('SELECT * FROM cache WHERE (task = ?) AND ((page_id = ?) OR (name = ?))', (task, name, name)).fetchone()
        if result:
            ret = {'id': result[0], 'task': result[1], 'name': result[2]}
            ret.update(json.loads(result[3]))
            return ret
        else:
            return None

    def set(self, task, info):
        page_id = info['pageid']
        name = info['title']
        info = json.dumps(info)
        self._db.execute('INSERT OR REPLACE INTO cache (page_id, task, name, info) VALUES (?,?,?,?)', (page_id, task, name, info))

    def close(self):
        self._db.commit()
        self._db.close()

    def iter_task(self, task):
        cur = self._db.execute('SELECT info from cache WHERE task = ?', (task,))
        while True:
            result = cur.fetchone()
            if result:
                yield json.loads(result[0])
            else:
                return
cache = Cache()
