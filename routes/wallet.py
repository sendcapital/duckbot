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
  QUERY_ROUTES,
  WALLET_ROUTES,
  MAIN_MENU,
  GEN_WALLET,
  FUND_WALLET,
  WALLET_MANAGEMENT,
)
from web3 import Web3
logger = init_logger(__name__)

class Wallet:
  def __init__(self, airdao_handler, config, w3):
    self.config = config
    self.w3: Web3.HTTPProvider = w3
    self.airdao_handler = airdao_handler
    self.main_menu = self.airdao_handler.main_menu_routes.get_main_menu()
    
  def update_user_event_manager(self, user_event_manager):
    self.user_event_manager = user_event_manager
    
  def get_wallet_keyboard(self):
    keyboard = [
      [
        InlineKeyboardButton("💰 Generate Wallet", callback_data=str(GEN_WALLET)),
        InlineKeyboardButton("💸 Fund Wallet", callback_data=str(FUND_WALLET)),
      ],
      [
        InlineKeyboardButton("⬅️ Go Back", callback_data=str(MAIN_MENU)),
      ]
    ]
    return keyboard
  
  async def wallet_management(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = ("Explore AirDao Wallets! What do you want to do?")
    keyboard = self.get_wallet_keyboard()
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
      await update.message.reply_text(text=text, reply_markup=reply_markup)
      
    elif update.callback_query:
      query = update.callback_query
      await query.message.edit_text(text=text, reply_markup=reply_markup)

    return WALLET_ROUTES
  
  async def handle_wallet_operation(self, update: Update, context: CallbackContext):
    operation = context.user_data.get('operation')
    if operation == 'gen':
      await self.gen_wallet(update, context)
    return WALLET_ROUTES

  async def gen_wallet_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    text = "Generate a new wallet! Please enter a name for your wallet."
    context.user_data['operation'] = 'gen'
    await query.message.reply_text(text=text, reply_markup=ForceReply())
    logger.info(f"User {query.from_user.id} is generating a new wallet.")
    return WALLET_ROUTES
  
  async def gen_wallet(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    wallet_name = update.message.text
    wallet = self.w3.eth.account.create()
    address = wallet.address
    private_key = wallet._private_key.hex()
    text = (
      f"Wallet generated successfully!\n"
      f"Name: {wallet_name}\n"
      f"Address: {address}\n"
      f"Private Key: {private_key}"
    )
    keyboard = self.get_wallet_keyboard()
    keyboard_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text=text, reply_markup=keyboard_markup)
    logger.info(f"Wallet generated successfully by {user_id}!")
    return WALLET_ROUTES
  
  async def fund_wallet_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    text = "Please enter the address you want to fund."
    await update.message.reply_text(text=text, reply_markup=ForceReply())
    logger.info(f"User {user_id} is funding a wallet.")
    return WALLET_ROUTES
  
  async def fund_wallet(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    message = update.message.text.split(" ")
    if len(message) == 0:
      text = "Invalid command format"
      await update.message.reply_text(text=text)
      return WALLET_ROUTES
    
    address = message[0].lower()
    checksum_address = self.w3.to_checksum_address(address)
    
    keyboard = self.get_wallet_keyboard()
    keyboard_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text=text, reply_markup=keyboard_markup)
    
    logger.info(f"User {user_id} is funding {address}.")
    return WALLET_ROUTES

  def get_handler(self):
    wallet_routes = [
      MessageHandler(filters.TEXT & filters.REPLY, self.handle_wallet_operation),
      CallbackQueryHandler(self.wallet_management, pattern=f"^{WALLET_MANAGEMENT}$"),
      CallbackQueryHandler(self.gen_wallet_help, pattern=f"^{GEN_WALLET}$",),
      CallbackQueryHandler(self.fund_wallet_help, pattern=f"^{FUND_WALLET}$",),
      CallbackQueryHandler(self.main_menu, pattern=f"^{MAIN_MENU}$"),
    ]
    wallet_routes.extend(self.airdao_handler.base_commands())
    return wallet_routes