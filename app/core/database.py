# https://www.cnblogs.com/ljhdo/p/10671273.html
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from urllib.parse import quote
from typing import Generator

from config import db_user, db_password, db_host, db_name
from logger import logger

encoded_password = quote(db_password)


DATABASE_URL = (
    f"mssql+pymssql://{db_user}:{encoded_password}@{db_host}/{db_name}?tds_version=7.0"
)
# logger.info(f"DATABASE_URL:{DATABASE_URL}")
engine = create_engine(DATABASE_URL)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_session() -> Generator:
    """
    获取数据库会话的依赖函数
    使用方法：
    session: Session = Depends(get_session)
    """
    from sqlmodel import Session

    with Session(engine) as session:
        yield session
