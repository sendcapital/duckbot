from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ForceReply, Chat
from telegram.ext import (
  CallbackQueryHandler,
  ContextTypes,
  filters,
  MessageHandler,
  CallbackContext,
  CommandHandler
)
from utils import (
  init_logger
)
from consts import (
  TRADE_ROUTES,
  SEND_FUNDS,
  MAIN_MENU,
  TRADE_MANAGEMENT,
)
from web3 import Web3
logger = init_logger(__name__)

class Trade:
  def __init__(self, airdao_handler, config, w3):
    self.config = config
    self.w3: Web3.HTTPProvider = w3
    self.airdao_handler = airdao_handler
    self.main_menu = self.airdao_handler.main_menu_routes.get_main_menu()
    
  def update_user_event_manager(self, user_event_manager):
    self.user_event_manager = user_event_manager
    
  def get_trade_keyboard(self):
    keyboard = [
      [
        InlineKeyboardButton("💰 Send funds", callback_data=str(SEND_FUNDS)),
      ],
      [
        InlineKeyboardButton("⬅️ Go Back", callback_data=str(MAIN_MENU)),
      ]
    ]
    return keyboard
  
  async def trade_management(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = ("Explore AirDao Wallets! What do you want to do?")
    keyboard = self.get_trade_keyboard()
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
      await update.message.reply_text(text=text, reply_markup=reply_markup)
      
    elif update.callback_query:
      query = update.callback_query
      await query.message.edit_text(text=text, reply_markup=reply_markup)

    return TRADE_ROUTES
  
  async def handle_trade_operation(self, update: Update, context: CallbackContext):
    operation = context.user_data.get('operation')
    if operation == 'send_funds':
      await self.send_funds(update, context)
    return TRADE_ROUTES

  async def send_funds_help(self, update: Update, context: CallbackContext):
    if update.callback_query:
      user_id = update.callback_query.from_user.id
      query = update.callback_query
      await query.answer()
    if update.message:
      user_id = update.message.from_user.id
      
    context.user_data['operation'] = 'send_funds'
    text = "Please enter the address you want to send funds to."
    await query.message.reply_text(text=text, reply_markup=ForceReply())
    logger.info(f"User {user_id} is funding a wallet")
    return TRADE_ROUTES
  
  async def send_funds(self, update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    pk = "2d4ff9a108d7e102e68a0eeda132303d07906f730264ec7b6e1f1cd9fc1440cd"
    address = "0x01a093700a7f67F42dc6590278887F5830D8AEeC"
    acct2 = self.w3.eth.account.from_key(pk)
    
    gas_limit = self.w3.eth.estimate_gas({
      'from': "0x01a093700a7f67F42dc6590278887F5830D8AEeC",
      'to': "0x7b2A074D95452897E9D53139DD6425Cdb2c2b9bb"
    })
    
    transaction = {
      'from': acct2.address,
      'to': "0x7b2A074D95452897E9D53139DD6425Cdb2c2b9bb",
      'value': 1,
      'nonce': self.w3.eth.get_transaction_count(acct2.address),
      'gas': gas_limit,
      'gasPrice': self.w3.eth.gas_price,
      'chainId': self.w3.eth.chain_id
    }
    signed = self.w3.eth.account.sign_transaction(transaction, pk)

    tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
    tx = self.w3.eth.get_transaction(tx_hash)    
    text = "Funds sent successfully!"

    keyboard = self.get_trade_keyboard()
    keyboard_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text=text, reply_markup=keyboard_markup)
    logger.info(f"User {user_id} is funding {address}.")
    return TRADE_ROUTES 
    

  def get_handler(self):
    wallet_routes = [
      MessageHandler(filters.TEXT & filters.REPLY, self.handle_trade_operation),
      CallbackQueryHandler(self.trade_management, pattern=f"^{TRADE_MANAGEMENT}$"),
      CallbackQueryHandler(self.send_funds_help, pattern=f"^{SEND_FUNDS}$",),
      CallbackQueryHandler(self.main_menu, pattern=f"^{MAIN_MENU}$"),
    ]
    wallet_routes.extend(self.airdao_handler.base_commands())
    return wallet_routes