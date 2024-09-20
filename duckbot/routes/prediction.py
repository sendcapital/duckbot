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
  PREDICTION_ROUTES,
  MAIN_MENU,
  PREDICTION_MANAGEMENT,
  SELECT_MARKET,
)
from web3 import Web3
logger = init_logger(__name__)

class Prediction:
  def __init__(self, airdao_handler, config, w3, cipher, db):
    self.config = config
    self.w3: Web3.HTTPProvider = w3
    self.airdao_handler = airdao_handler
    self.db = db
    self.wallet_interface = self.db.wallet_interface
    self.cipher = cipher
    self.main_menu = self.airdao_handler.main_menu_routes.get_main_menu()
    
  def get_prediction_keyboard(self):
    keyboard = [
      [ 
        InlineKeyboardButton("⚽ Sports", callback_data="category_sports"),
        InlineKeyboardButton("🌐 Politics", callback_data="category_politics"),
      ],
      [
        InlineKeyboardButton("📈 Crypto", callback_data="category_crypto"),
        InlineKeyboardButton("📊 Business", callback_data="category_business"),
      ],
      [
        InlineKeyboardButton("⬅️ Go Back", callback_data=str(MAIN_MENU)),
      ]
    ]
    return keyboard
  
  async def prediction_management(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = ("🔮 What will you predict today? You can predict on sports, elections, crypto prices, and more.\n" +
            "Ready to make your first prediction? Type /predict to start!")
    keyboard = self.get_prediction_keyboard()
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
      await update.message.reply_text(text=text, reply_markup=reply_markup)
      
    elif update.callback_query:
      query = update.callback_query
      await query.message.edit_text(text=text, reply_markup=reply_markup)

    return PREDICTION_ROUTES
  
  async def handle_prediction_operation(self, update: Update, context: CallbackContext):
    operation = context.user_data.get('operation')
    if operation == 'send_funds':
      await self.send_funds(update, context)
    return PREDICTION_ROUTES
  
  async def predict_category(self, update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    if query.data.startswith("category_"):
      category = str(query.data.split("_")[-1]) 
      text = f"📈 {category} Category\n"
      keyboard = [
        [
          InlineKeyboardButton("🔮 Predict", callback_data="predict"),
          InlineKeyboardButton("📊 Market Info", callback_data="market_info"),
        ],
        [
          InlineKeyboardButton("⬅️ Go Back", callback_data=str(PREDICTION_MANAGEMENT)),
        ]
      ]
      reply_markup = InlineKeyboardMarkup(keyboard)
      await query.message.reply_text(text=text, reply_markup=reply_markup)
      
    return PREDICTION_ROUTES

  def get_handler(self):
    prediction_routes = [
      MessageHandler(filters.TEXT & filters.REPLY, self.handle_prediction_operation),
      CallbackQueryHandler(self.prediction_management, pattern=f"^{PREDICTION_MANAGEMENT}$"),
      CallbackQueryHandler(self.predict_category, pattern=f"^category_.+$"),
      CallbackQueryHandler(self.main_menu, pattern=f"^{MAIN_MENU}$"),
    ]
    prediction_routes.extend(self.airdao_handler.base_commands())
    return prediction_routes