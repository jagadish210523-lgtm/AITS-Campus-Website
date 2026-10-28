import os
print("DB_HOST exists:", "DB_HOST" in os.environ)
from urllib.parse import quote_plus

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DB_HOST = os.environ["DB_HOST"]
DB_PORT = os.environ.get("DB_PORT", "3306")
DB_USER = os.environ["DB_USER"]
DB_PASSWORD = os.environ["DB_PASSWORD"]
DB_NAME = os.environ.get("DB_NAME", "defaultdb")
DB_SSL_CA = os.environ.get("DB_SSL_CA", "/etc/secrets/ca.pem")

URL_DATABASE = (
    f"mysql+pymysql://{quote_plus(DB_USER)}:{quote_plus(DB_PASSWORD)}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

engine = create_engine(
    URL_DATABASE,
    connect_args={"ssl": {"ca": DB_SSL_CA}},
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    autocommit=False,
)
Base = declarative_base()