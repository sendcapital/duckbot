from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Enum, Index, BigInteger, ForeignKey, PrimaryKeyConstraint, ARRAY
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime, timezone
from dataclasses import dataclass
from .base import Base

@dataclass
class Market(Base):
  __tablename__ = 'markets'
  market_id = Column(Integer, nullable=False)
  book = Column(ARRAY(Integer), nullable=False)
  price_tick = Column(Integer, nullable=False)
  ask_index = Column(Integer, nullable=False)
  market_name = Column(String(255), nullable=False)
  category = Column(String(255), nullable=False)
  market_close = Column(Boolean, nullable=False)
  created_at = Column(DateTime, nullable=False)
  closed_at = Column(DateTime, nullable=False)

  __table_args__ = (
    PrimaryKeyConstraint('market_id'),
  )
  positions = relationship("Position", back_populates="market")
