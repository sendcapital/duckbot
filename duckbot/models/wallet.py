from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Enum, Index, BigInteger, ForeignKey, PrimaryKeyConstraint
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime, timezone

from .base import Base

class Wallet(Base):
  __tablename__ = 'wallets'

  telegram_user_id = Column(Integer, ForeignKey('users.telegram_user_id'), nullable=False)
  address = Column(String(255), nullable=False)
  label = Column(String(255), nullable=False)
  encrypted_key = Column(String(300), nullable=False)

  __table_args__ = (
    PrimaryKeyConstraint('telegram_user_id', 'address'),
  )
  
  user = relationship("User", back_populates="wallets")