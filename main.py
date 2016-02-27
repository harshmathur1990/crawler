from gevent import monkey
monkey.patch_all()
import gevent
from gevent.wsgi import WSGIServer
from gevent.queue import Queue
from flask import Flask
from database import db_session
from bs4 import BeautifulSoup
from urllib2 import urlopen, HTTPError, URLError
from models import Url
import httplib
app = Flask(__name__)
url_visited = dict()

@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()

def get_effective_end_point(end_point):
    if end_point:
        end_point = end_point.strip()
    if not end_point:
        return None
    if end_point == '/' or end_point.startswith('javascript') or end_point.startswith('#'):
        return None
    return end_point


def perist_and_update_child_urls(url, childUrlQueue):
    try:
        # print "perist_and_update_child_urls started"
        # print "opening", url
        opened_url = urlopen(url)
        # print "opened", url
        u = Url(url)
        # print "db.add", url
        db_session.add(u)
        # print "db.commit", url
        db_session.commit()
        # print "db.done", url
        try:
            page = opened_url.read()
            # print "page read ", url
        except httplib.IncompleteRead, e:
            page = e.partial
            # print "page partially read ", url
        soup = BeautifulSoup(page, 'html.parser')
        # print "parsed into BeautifulSoup ", url
        links = soup.find_all('a')
        # print "found all child links for ", url
        for link in links:
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
                # print "about to add in queue ",child_url
                try:
                    childUrlQueue.put_nowait(child_url)
                except gevent.queue.Queue.Full:
                    # print "blocking until we put into the queue ", child_url
                    childUrlQueue.put(child_url)
                # print "added in queue ",child_url
        # print "perist_and_update_child_urls completed"
    except HTTPError as e:
        u = Url(url, unicode(e.code))
        db_session.add(u)
        db_session.commit()
    except URLError as e:
        u = Url(url, unicode(e.reason))
        db_session.add(u)
        db_session.commit()
    except Exception as e:
        print e


@app.route("/")
def hello():
    url = 'http://askme.com'
    # url_visited = dict()
    main_queue = Queue()
    main_queue.put(url)
    depth = 0
    max_depth = 3
    max_url_count = 10000
    while not main_queue.empty() and depth <= max_depth:
        # print main_queue
        # print "depth: ", depth
        child_url_queue = Queue()
        threads = list()
        while not main_queue.empty():
            element = main_queue.get()
            if not url_visited.get(element, False):
                threads.append(
                    gevent.spawn(
                        perist_and_update_child_urls, element, child_url_queue
                        ))
                url_visited[element] = True
        # print "entering wait mode"
        gevent.joinall(threads)
        depth = depth + 1
        # print "depth after increment: ", depth
        if len(url_visited.keys()) < max_url_count:
            main_queue = child_url_queue
    return "Hello World!"

if __name__ == "__main__":
    http_server = WSGIServer(('', 8000), app)
    http_server.serve_forever()
