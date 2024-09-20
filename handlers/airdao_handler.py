#!/usr/bin/env python
# -*- coding: utf-8 -*-
from warnings import filterwarnings
import time
import redis
import asyncio
from functools import wraps
import numpy as np
from datetime import datetime, timezone
from web3 import Web3
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ForceReply, Chat
from telegram.warnings import PTBUserWarning
from telegram.ext import (
  CallbackQueryHandler,
  CommandHandler,
  ContextTypes,
  ConversationHandler,
  CallbackContext,
  Application
)

from utils import (
  init_logger
)

from consts import (
  QUERY_ROUTES,
  END_ROUTES,
  MAIN_MENU,
  EXPLORER_MANAGEMENT,
  EXPLORER_ROUTES,
  WALLET_ROUTES,
  WALLET_MANAGEMENT
)

from routes import (
  MainMenu, 
  Explorer,
  Wallet
)

filterwarnings(action="ignore", message=r".*CallbackQueryHandler", category=PTBUserWarning)
logger = init_logger(__name__)

class AirDaoHandler:
  def __init__(self, application, config):
    self.config = config
    self.application: Application = application
    
    self.user_id = None
    self.chat_id = None
    self.main_menu_routes = MainMenu(self)
    self.main_menu = self.main_menu_routes.get_main_menu()
    
    self.explorer_routes = Explorer(self, self.config)
    self.explorer_management = self.explorer_routes.explorer_management
    
    self.wallet_routes = Wallet(self, self.config)
    self.wallet_management = self.wallet_routes.wallet_management
    asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy()) # Fix RuntimeError: There is no current event loop in thread 'Thread-1'.
        
  async def start(
    self, 
    update: Update, 
    context: ContextTypes.DEFAULT_TYPE
  ) -> int:
    user = update.message.from_user
    self.first_name = user.first_name if user.first_name else "None"
    self.user_id = user.id
    self.language_code = user.language_code
    self.username = user.username if user.username else "None"
    self.is_bot = user.is_bot
    self.chat_id = update.message.from_user.id
    self.chat_type = update.message.chat.type
    await self.application.bot.send_message(chat_id=self.chat_id, text="Pulling archives and magic ✨ from the void ...")
    logger.info("User %s started the conversation.", user.first_name)
    await self.main_menu(update, context)
    return QUERY_ROUTES
  
  async def exit(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    keyboard = [
      [
        InlineKeyboardButton("Yes, let's do it again!", callback_data=str(QUERY_ROUTES)),
        InlineKeyboardButton("Nah, I've had enough ...", callback_data=str(END_ROUTES)),
      ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
      text="Are you sure you want to end the session?", reply_markup=reply_markup
    )
    
    return END_ROUTES


  async def end(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    End the conversation and display the final message.
    
    Args:
        update (telegram.Update): The update object.
        context (telegram.ext.ContextTypes.DEFAULT_TYPE): The context object.
    
    Returns:
        int: The next conversation stage.
    """
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text="See you next time!")
    return ConversationHandler.END
  
  def get_explorer_route(self):
    return self.explorer_routes.get_handler()
  
  def get_wallet_route(self):
    return self.wallet_routes.get_handler()
  
  def base_commands(self):
    return [
      CommandHandler("main_menu", self.main_menu),
    ]


  def create_conversation_handler(self) -> ConversationHandler:
    bundled_query_routes = [
      CallbackQueryHandler(self.main_menu, pattern=f"^{MAIN_MENU}$"),
      CallbackQueryHandler(self.explorer_management, pattern=f"^{EXPLORER_MANAGEMENT}$"),
      CallbackQueryHandler(self.wallet_management, pattern=f"^{WALLET_MANAGEMENT}$"),

    ]
    return ConversationHandler(
      entry_points=[CommandHandler("start", self.start)],
      states={
        QUERY_ROUTES: bundled_query_routes,
        EXPLORER_ROUTES: self.get_explorer_route(),
        WALLET_ROUTES: self.get_wallet_route(),
        END_ROUTES: [CallbackQueryHandler(self.end, pattern=f"^{END_ROUTES}$")],
      },
      fallbacks=[CommandHandler("start", self.start)],
      name="airdao_conversation",
    )
