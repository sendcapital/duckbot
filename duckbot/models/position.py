from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Enum, Index, BigInteger, ForeignKey, PrimaryKeyConstraint, ARRAY
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime, timezone

from .base import Base

class Position(Base):
  __tablename__ = 'positions'
  telegram_user_id = Column(BigInteger, ForeignKey('users.telegram_user_id'), nullable=False)
  market_id = Column(Integer, ForeignKey('markets.market_id'), nullable=False)
  size = Column(Integer, nullable=False)
  notional = Column(Integer, nullable=False)
  prediction = Column(Integer, nullable=False)
  timestamp = Column(DateTime, nullable=False)

  __table_args__ = (
    PrimaryKeyConstraint('telegram_user_id', 'market_id'),
  )
  
  user = relationship("User", back_populates="positions")
  market = relationship("Market", back_populates="positions")