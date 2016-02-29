from sqlalchemy import Table, Column, Integer, String
from database import metadata



urls = Table('url', metadata,
             Column('id', Integer, primary_key=True),
             Column('url', String(100), unique=True),
             Column('code', String(100)),
             )
