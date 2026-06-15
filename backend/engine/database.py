from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

class Scan(Base):
    __tablename__ = "scans"

    id = Column(Integer, primary_key=True)
    ip = Column(String)
    ports = Column(String)
    risk = Column(Float)

engine = create_engine("sqlite:///reaper.db")
Session = sessionmaker(bind=engine)
Base.metadata.create_all(engine)
