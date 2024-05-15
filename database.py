from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base

DATABASE_URL = 'sqlite:///database.sqlite'
engine = create_engine(DATABASE_URL+"?check_same_thread=true", echo=False)
Session = sessionmaker(bind=engine)

def create_database():
    Base.metadata.create_all(engine)

if __name__ == '__main__':
    create_database()
    