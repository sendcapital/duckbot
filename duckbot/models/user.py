from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Enum, Index, BigInteger
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime, timezone
from dataclasses import dataclass
from .base import Base

@dataclass
class User(Base):
  __tablename__ = 'users'

  id = Column(Integer, primary_key=True, autoincrement=True)
  created_at = Column(DateTime, default=datetime.now(timezone.utc))
  updated_at = Column(DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
  telegram_user_id = Column(BigInteger, unique=True, nullable=False)
  telegram_username = Column(String, nullable=False)
  language_code = Column(String, nullable=True)
  bot = Column(Boolean, default=False)
  
  __table_args__ = (
    Index('index_users_on_telegram_user_id', 'telegram_user_id'),
  )

  wallets = relationship("Wallet", back_populates="user")
  positions = relationship("Position", back_populates="user")
