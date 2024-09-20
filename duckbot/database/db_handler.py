import sys
import csv
import logging
from io import StringIO
from dataclasses import dataclass
import json
from models import (
  User, 
  Wallet
)
from decimal import Decimal
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import func, create_engine, select, update, desc, delete
from utils import init_logger

logger = init_logger(__name__)


@dataclass
class BaseQuery:
  session: sessionmaker

  def get_row_by_query(self, query) -> tuple:
    try:
      result = self.session.execute(query).fetchone()
      return result if result else None
    except Exception as e:
      logger.error(f"Error executing query: {e}")
      self.session.rollback()
      raise
    
  def get_rows_by_query(self, query) -> tuple:
    try:
      result = self.session.execute(query).fetchall()
      return result if result else None
    except Exception as e:
      logger.error(f"Error executing query: {e}")
      self.session.rollback()
      raise

  def execute_query_and_commit(self, query) -> None:
    try:
      self.session.execute(query)
      self.session.commit()
    except Exception as e:
      logger.error(f"Error executing query: {e}")
      self.session.rollback()
      raise
    

class UserInterface(BaseQuery):

  def _exists(self, telegram_user_id: str) -> bool:
    query = select(User).where(User.telegram_user_id == int(telegram_user_id))
    try:
      result = self.get_row_by_query(query)
      if result:
        return result
      return None
    except Exception as e:
      logger.error(f"Error checking if user exists: {e}")
      raise

  def create_if_not_exists(self, telegram_user_id: str, **kwargs) -> bool:
    if self._exists(telegram_user_id) == None:
      new_user = User(telegram_user_id=int(telegram_user_id), **kwargs)
      try:
        self.session.add(new_user)
        self.session.commit()
        logger.info(f'User created: {kwargs}')
        return True
      except Exception as e:
        logger.error(f"Error creating user: {e}")
        self.session.rollback()
        raise
    else:
      logger.info(f'User already exists with telegram_user_id: {telegram_user_id}')
    return False
   
  def fetch_user_data(self, telegram_user_id: str = None) -> tuple:
    query = select(User).where(User.telegram_user_id == telegram_user_id)
    try:
      logger.info(f'Getting user with telegram_user_id: {telegram_user_id}')
      result = self.get_row_by_query(query)
      return result
    except Exception as e:
      logger.error(f"Error getting user: {e}")
      raise
  
  def update_user_data(self, telegram_user_id: str = None, **kwargs) -> None:
    if self._exists(telegram_user_id):
      query = update(User).where(User.telegram_user_id == telegram_user_id).values(**kwargs)
      try:
        self.execute_query_and_commit(query)
        logger.info(f'User updated: {kwargs}')
      except Exception as e:
        logger.error(f"Error updating user: {e}")
        self.session.rollback()
        raise
    else:
      logger.info(f'User does not exist with telegram_user_id: {telegram_user_id}')
      self.create_if_not_exists(telegram_user_id=str(telegram_user_id), **kwargs)

class WalletInterface(BaseQuery):     
  def create_if_not_exists(self, user_id: str, address: str, label: str, **kwargs) -> bool:
    query = select(Wallet).where(Wallet.telegram_user_id == user_id, Wallet.label == label)
    try:
      result = self.get_row_by_query(query)
      if result:
        logger.info(f'Wallet already exists with user_id: {user_id} and label: {label}')
        return False
      new_wallet = Wallet(telegram_user_id=user_id, address=address, label=label, **kwargs)
      self.session.add(new_wallet)
      self.session.commit()
      logger.info(f'Wallet created: {kwargs}')
      return True
    except Exception as e:
      logger.error(f"Error creating wallet: {e}")
      self.session.rollback()

  def fetch_wallet_data(self, user_id: str):
    query = select(Wallet).where(Wallet.telegram_user_id == user_id)
    try:
      logger.info(f'Getting wallet with user_id: {user_id}')
      result = self.get_row_by_query(query)
      return result[0]
    except Exception as e:
      logger.error(f"Error getting wallet: {e}")
      raise

  def fetch_wallet_bool(self, user_id: str) -> bool:
    query = select(Wallet).where(Wallet.telegram_user_id == user_id)
    try:
      logger.info(f'Getting wallet with user_id: {user_id}')
      result = self.get_row_by_query(query)
      return True if result else False
    except Exception as e:
      logger.error(f"Error getting wallet: {e}")
      raise
  
  def delete_wallet(self, user_id: str, label: str) -> None:
    query = delete(Wallet).where(Wallet.telegram_user_id == user_id, Wallet.label == label)
    try:
      self.execute_query_and_commit(query)
      logger.info(f'Wallet deleted with user_id: {user_id} and label: {label}')
    except Exception as e:
      logger.error(f"Error deleting wallet: {e}")
      self.session.rollback()
      raise

class AirDaoDB:

  def __init__(self):
    self.db_url = "postgresql://postgres:postgres@localhost:5439/duckbot_local"
    logger.info(f"Connecting to database at {self.db_url} on test")
      
    self.engine = create_engine(self.db_url, pool_size=10, max_overflow=20)
    self.Session = sessionmaker(bind=self.engine)
    self.session = self.Session()

    self.user_interface = UserInterface(self.session)
    self.wallet_interface = WalletInterface(self.session)
    
    
  def open_connection(self):
    """Connection management is handled by SQLAlchemy."""
    logger.info('Connection opened successfully.')

