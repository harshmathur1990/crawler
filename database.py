from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(
    'mysql+pymysql://root:root@localhost/crawler',
    convert_unicode=True)

metadata = MetaData()

