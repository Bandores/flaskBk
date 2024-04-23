from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine('sqlite:///events.db', echo=True)

Session = sessionmaker(bind=engine)
session = Session()

# Import your models here
from app import Base, User, Event, RatingComment

Base.metadata.create_all(engine)
