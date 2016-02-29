from gevent import monkey
monkey.patch_all()
import gevent
from gevent.wsgi import WSGIServer
from flask import Flask
from database import engine
from bs4 import BeautifulSoup
from urllib2 import urlopen, HTTPError, URLError
from models import urls
import httplib
app = Flask(__name__)
url_visited = dict()


def get_effective_end_point(end_point):
    if end_point:
        end_point = end_point.strip()
    if not end_point:
        return None
    if end_point == '/' or end_point.startswith('javascript') or end_point.startswith('#'):
        return None
    return end_point


def parent_and_run_child_urls(url, depth, max_depth):
    try:
        opened_url = urlopen(url)
        url_insert = urls.insert()\
            .values(url=url, code=u'200')
        conn = engine.connect()
        conn.execute(url_insert)
        conn.close()
        try:
            page = opened_url.read()
        except httplib.IncompleteRead, e:
            page = e.partial
        soup = BeautifulSoup(page, 'html.parser')
        links = soup.find_all('a')
        threads = list()
        child_depth = int(depth) + int(1)
        print child_depth
        for link in links:
            if not depth > max_depth and not len(url_visited.keys()) > 10000:
                end_point = link.get('href')
                effective_end_point = get_effective_end_point(end_point)
                if effective_end_point and effective_end_point.startswith('/'):
                    if not url.endswith('/'):
                        child_url = url + effective_end_point
                    else:
                        child_url = url[:-1] + effective_end_point
                else:
                    child_url = effective_end_point
                if child_url and not url_visited.get(child_url, False):
                    threads.append(gevent.spawn(parent_and_run_child_urls, child_url, child_depth, max_depth))
            else:
                pass
        if threads:
            gevent.joinall(threads)
    except HTTPError as e:
        url_insert = urls.insert()\
            .values(url=url, code=unicode(e.reason))
        conn = engine.connect()
        conn.execute(url_insert)
        conn.close()
    except URLError as e:
        url_insert = urls.insert()\
            .values(url=url, code=unicode(e.reason))
        conn = engine.connect()
        conn.execute(url_insert)
        conn.close()
    except Exception as e:
        print e


@app.route("/")
def new_dfs_based_crawling():
    url = 'http://askme.com'
    depth = 0
    max_depth = 3
    threads = list()
    threads.append(gevent.spawn(parent_and_run_child_urls, url, depth, max_depth))
    gevent.joinall(threads)
    return "Hello World!"


if __name__ == "__main__":
    app.debug = True
    http_server = WSGIServer(('', 8000), app)
    http_server.serve_forever()
