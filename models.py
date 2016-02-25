from sqlalchemy import Table, Column, Integer, String
from sqlalchemy.orm import mapper
from database import metadata, db_session


class Url(object):
    query = db_session.query_property()

    def __init__(self, url, code=u'200'):
        self.url = url
        self.code = code

    def __repr__(self):
        return '<Url %r>' % (self.url)

urls = Table('url', metadata,
             Column('id', Integer, primary_key=True),
             Column('url', String(100), unique=True),
             Column('code', String(100)),
             )

mapper(Url, urls)
