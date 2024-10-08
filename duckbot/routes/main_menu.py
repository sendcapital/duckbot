#!/usr/bin/env python
# -*- coding: utf-8 -*-
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
  CallbackContext,
  ContextTypes
)
from consts import (
  QUERY_ROUTES, 
  TRADE_MANAGEMENT,
  WALLET_MANAGEMENT,
  EXPLORER_MANAGEMENT,
  PREDICTION_MANAGEMENT
)

from utils import (
  init_logger
)
logger = init_logger(__name__)


class MainMenu:
  def __init__(self, portfolio_handler):
    self.name = "main_menu"
    self.routes = {
      "main_menu": self.main_menu,
    }
    self.portfolio_handler = portfolio_handler
    
  def get_main_menu_keyboard(self):
    keyboard = [
      [
        InlineKeyboardButton("📈 Prediction Market", callback_data=str(PREDICTION_MANAGEMENT)),
        InlineKeyboardButton("💰 Manage Wallets", callback_data=str(WALLET_MANAGEMENT)),
      ],
      [
        InlineKeyboardButton("📈 Trade AirDao", callback_data=str(TRADE_MANAGEMENT)),
        InlineKeyboardButton("🌐 AirDao Explorer", callback_data=str(EXPLORER_MANAGEMENT))
      ],
    ]
    return keyboard
  
  async def main_menu(self, update: Update,  context: ContextTypes.DEFAULT_TYPE):
    keyboard = self.get_main_menu_keyboard()
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = (
      "🦆 Welcome to Duck Bot 🦆\n"
      "AirDAO's Prediction Market on Telegram!\n"
      "\n"
      "Start trading in 3 easy steps:\n"
      "1. Generate and fund a new wallet under Manage Wallets\n"
      "2. Choose a market under Prediction Market\n"
      "3. Place your bets!\n"
    )
    if update.message:
      await update.message.reply_text(text=text, reply_markup=reply_markup)
      
    elif update.callback_query:
      query = update.callback_query
      await query.message.edit_text(text=text, reply_markup=reply_markup)
    return QUERY_ROUTES
  
  def get_main_menu(self):
    return self.routes["main_menu"]
  