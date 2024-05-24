from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from models import Base

DATABASE_URL = 'sqlite:///database.sqlite'
engine = create_engine(DATABASE_URL, echo=False)
session_maker = sessionmaker(bind=engine)
Session = scoped_session(session_maker)

def create_database():
    Base.metadata.create_all(engine)

if __name__ == '__main__':
    create_database()
    