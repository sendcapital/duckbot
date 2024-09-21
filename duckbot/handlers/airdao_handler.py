#!/usr/bin/env python
# -*- coding: utf-8 -*-
from warnings import filterwarnings
import asyncio
from web3 import Web3
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ForceReply, Chat
from telegram.warnings import PTBUserWarning
from telegram.ext import (
  CallbackQueryHandler,
  CommandHandler,
  ContextTypes,
  ConversationHandler,
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
  WALLET_MANAGEMENT,
  TRADE_ROUTES,
  TRADE_MANAGEMENT,
  PREDICTION_ROUTES,
  PREDICTION_MANAGEMENT
)

from routes import (
  MainMenu, 
  Explorer,
  Wallet,
  Trade,
  Prediction
)

from utils import AESCipher

filterwarnings(action="ignore", message=r".*CallbackQueryHandler", category=PTBUserWarning)
logger = init_logger(__name__)

class AirDaoHandler:
  def __init__(self, application, config, db):
    self.config = config
    self.application: Application = application
    self.db = db
    self.user_id = None
    self.chat_id = None
    self.main_menu_routes = MainMenu(self)
    self.main_menu = self.main_menu_routes.get_main_menu()
    self.w3 = Web3(Web3.HTTPProvider(self.config["airdao_main_rpc"]))
    self.cipher = None
    
    self.user_interface = self.db.user_interface
    
    self.explorer_routes = Explorer(self, self.config, self.w3)
    self.explorer_management = self.explorer_routes.explorer_management
    
    self.wallet_routes = Wallet(self, self.config, self.cipher, self.db)
    self.wallet_management = self.wallet_routes.wallet_management
    
    self.trade_routes = Trade(self, self.config, self.w3, self.cipher, self.db)
    self.trade_management = self.trade_routes.trade_management
    
    self.prediction_routes = Prediction(self, self.config, self.cipher, self.db)
    self.prediction_management = self.prediction_routes.prediction_management
    
    asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy()) # Fix RuntimeError: There is no current event loop in thread 'Thread-1'.
        
  async def start(
    self, 
    update: Update, 
    context: ContextTypes.DEFAULT_TYPE
  ) -> int:
    user = update.message.from_user
    self.first_name = user.first_name if user.first_name else "None"
    self.user_id = user.id
    self.cipher = AESCipher(str(self.user_id), self.config)
    self.wallet_routes.cipher = self.cipher
    self.trade_routes.cipher = self.cipher

    self.language_code = user.language_code
    self.username = user.username if user.username else "None"
    self.is_bot = user.is_bot
    self.chat_id = update.message.from_user.id
    self.chat_type = update.message.chat.type

    self.user_data = self.user_interface.fetch_user_data(telegram_user_id=self.user_id)
    if self.user_data == None:
      self.user_interface.create_if_not_exists(
        telegram_user_id=self.user_id,
        telegram_username=self.username,
        language_code=self.language_code,
        bot=self.is_bot
      )
      
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
  
  def get_trade_route(self):
    return self.trade_routes.get_handler()

  def get_prediction_route(self):
    return self.prediction_routes.get_handler()
  
  def base_commands(self):
    return [
      CommandHandler("main_menu", self.main_menu),
    ]

  def create_conversation_handler(self) -> ConversationHandler:
    bundled_query_routes = [
      CallbackQueryHandler(self.main_menu, pattern=f"^{MAIN_MENU}$"),
      CallbackQueryHandler(self.explorer_management, pattern=f"^{EXPLORER_MANAGEMENT}$"),
      CallbackQueryHandler(self.wallet_management, pattern=f"^{WALLET_MANAGEMENT}$"),
      CallbackQueryHandler(self.trade_management, pattern=f"^{TRADE_MANAGEMENT}$"),
      CallbackQueryHandler(self.prediction_management, pattern=f"^{PREDICTION_MANAGEMENT}$"),
    ]
    return ConversationHandler(
      entry_points=[CommandHandler("start", self.start)],
      states={
        QUERY_ROUTES: bundled_query_routes,
        EXPLORER_ROUTES: self.get_explorer_route(),
        WALLET_ROUTES: self.get_wallet_route(),
        TRADE_ROUTES: self.get_trade_route(),
        PREDICTION_ROUTES: self.get_prediction_route(),
        END_ROUTES: [CallbackQueryHandler(self.end, pattern=f"^{END_ROUTES}$")],
      },
      fallbacks=[CommandHandler("start", self.start)],
      name="airdao_conversation",
    )
