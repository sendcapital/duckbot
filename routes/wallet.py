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
  WALLET_MANAGEMENT,
)
logger = init_logger(__name__)

class Wallet:
  def __init__(self, airdao_handler, config):
    self.config = config
    self.airdao_handler = airdao_handler
    self.main_menu = self.airdao_handler.main_menu_routes.get_main_menu()
    
  def update_user_event_manager(self, user_event_manager):
    self.user_event_manager = user_event_manager
    
  def get_wallet_keyboard(self):
    keyboard = [
      [
        InlineKeyboardButton("💰 Generate Wallet", callback_data=str(GEN_WALLET)),
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
  
  async def gen_wallet_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    text = "Generate a new wallet! Please enter a name for your wallet."
    await query.message.reply_text(text=text, reply_markup=ForceReply())
    return WALLET_ROUTES

  async def handle_wallet_operation(self, update: Update, context: CallbackContext):
    operation = context.user_data.get('operation')
    if operation == 'add':
      await self.add_wallet(update, context)
    elif operation == 'delete':
      await self.delete_wallet(update, context)
    return WALLET_ROUTES

  def get_handler(self):
    wallet_routes = [
      MessageHandler(filters.TEXT & filters.REPLY, self.handle_wallet_operation),
      CallbackQueryHandler(self.wallet_management, pattern=f"^{WALLET_MANAGEMENT}$"),
      CallbackQueryHandler(self.gen_wallet_help, pattern=f"^{GEN_WALLET}$",),
      CallbackQueryHandler(self.main_menu, pattern=f"^{MAIN_MENU}$"),
    ]
    wallet_routes.extend(self.airdao_handler.base_commands())
    return wallet_routes