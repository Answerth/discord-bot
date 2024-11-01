# models.py
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

DATABASE_URL = "postgresql://discordbotuser:discordbotuser@localhost/discordbotdb"

Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class ActivityLog(Base):
    __tablename__ = 'activity_log'

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    action = Column(String(250))
    details = Column(Text)

#class YourOtherTables(Base):
    # Define other tables as needed
#    pass

def init_db():
    Base.metadata.create_all(bind=engine)

