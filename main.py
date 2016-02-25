from gevent import monkey
monkey.patch_all()
import gevent
from gevent.wsgi import WSGIServer
from gevent.queue import Queue
from flask import Flask
from database import db_session
from lxml.html import parse
from urllib2 import urlopen, HTTPError, URLError
from models import Url
import sqlite3

app = Flask(__name__)


@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()


def complete_url(base_url, item, childUrlQueue):
    end_point = item.get('href')
    if not end_point.startswith('http'):
        url = base_url + end_point
    else:
        url = end_point
    childUrlQueue.put(url)


def perist_and_update_child_urls(url, childUrlQueue):
    print "inside perist_and_update_child_urls, ", url
    try:
        page = urlopen(url)
        u = Url(url)
        parsed = parse(page)
        doc = parsed.getroot()
        links = doc.findall('.//a')
        for link in links:
            end_point = link.get('href')
            if not end_point.startswith('http') and \
                    not end_point.startswith('www'):
                url = url + end_point
            else:
                url = end_point
            childUrlQueue.put(url)
    except HTTPError as e:
        u = Url(url, unicode(e.code))
    except URLError as e:
        u = Url(url, unicode(e.reason))
    try:
        db_session.add(u)
        db_session.commit()
    except sqlite3.IntegrityError as e:
        print e.message


@app.route("/")
def hello():
    url = 'http://askme.com'
    url_visited = dict()
    main_queue = Queue()
    main_queue.put(url)
    depth = 0
    max_depth = 3
    max_url_count = 10000
    while not main_queue.empty() and depth <= max_depth:
        print "in main while loop, ", main_queue.peek()
        child_url_queue = Queue()
        threads = list()
        while not main_queue.empty():
            element = main_queue.get()
            print "in inside while loop, ", element
            if not url_visited.get(element, False):
                threads.append(
                    gevent.spawn(
                        perist_and_update_child_urls, element, child_url_queue
                        ))
                url_visited[element] = True
        print "value of threads array, ", len(threads)
        gevent.joinall(threads)
        depth = depth + 1
        if len(url_visited.keys()) < max_url_count:
            main_queue = child_url_queue
    print url_visited
    return "Hello World!"

if __name__ == "__main__":
    http_server = WSGIServer(('', 8000), app)
    http_server.serve_forever()
