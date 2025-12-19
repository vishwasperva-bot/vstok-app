from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)

    # encrypted fields
    telegram_chat_id = Column(String, nullable=True)
    whatsapp_number = Column(String, nullable=True)

    # alert control (seconds)
    alert_interval = Column(Integer, default=300)
