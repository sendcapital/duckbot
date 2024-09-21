import asyncio
from aiohttp import ClientSession
from async_timeout import timeout
import ssl
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
  init_logger,
  fetch_eth_balance
)
from consts import (
  QUERY_ROUTES,
  WALLET_ROUTES,
  MAIN_MENU,
  GEN_WALLET,
  FUND_WALLET,
  PRIVATE_KEY,
  WALLET_MANAGEMENT,
)
from web3 import Web3
logger = init_logger(__name__)

class Wallet:
  def __init__(self, airdao_handler, config, cipher, db):
    self.config = config
    self.w3: Web3.HTTPProvider = Web3(Web3.HTTPProvider(self.config["airdao_test_rpc"]))
    self.airdao_handler = airdao_handler
    self.cipher = cipher
    self.db = db
    self.wallet_interface = self.db.wallet_interface
    self.main_menu = self.airdao_handler.main_menu_routes.get_main_menu()
    self.wallet_semaphore = asyncio.Semaphore(64)
    self.sslcontext = ssl.create_default_context()

    
  def get_wallet_keyboard(self, user_id):
    existing_wallet = self.wallet_interface.fetch_wallet_bool(user_id=user_id)
    if existing_wallet:
      keyboard = [
        [
          InlineKeyboardButton("💰 Reset Wallet", callback_data=str(GEN_WALLET)),
          InlineKeyboardButton("💸 Fund Wallet", callback_data=str(FUND_WALLET)),
        ],
        [
          InlineKeyboardButton("⬅️ Get Private Key", callback_data=str(PRIVATE_KEY)),
        ],
        [
          InlineKeyboardButton("⬅️ Go Back", callback_data=str(MAIN_MENU)),
        ]
      ]
      return keyboard
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
    user_id = update.callback_query.from_user.id
    wallet_exists = self.wallet_interface.fetch_wallet_bool(user_id=user_id)
    if wallet_exists:
      wallet_data = self.wallet_interface.fetch_wallet_data(user_id=user_id)
      address = wallet_data.address
      label = wallet_data.label
      balance = fetch_eth_balance(self.w3, address)
      text += (
        f"\n\nLabel: {label}\n"
        f"Address: {address}\n"
        f"Balance: {balance} AMB"
      )
      
    
    user_id = update.callback_query.from_user.id

    keyboard = self.get_wallet_keyboard(user_id)
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
    if operation == 'fund':
      await self.fund_wallet(update, context)
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
    
    existing_wallet = self.wallet_interface.fetch_wallet_bool(user_id=user_id)
    if not existing_wallet:
      address, pk_tuple = self.cipher.create_wallet()
      print(len(pk_tuple))
      encrypted_private_key = pk_tuple[0]
      
      self.wallet_interface.create_if_not_exists(
        user_id=user_id,
        address=address,
        label=wallet_name,
        encrypted_key=str(encrypted_private_key)
      )
    else:
      existing_wallet = self.wallet_interface.fetch_wallet_data(user_id=user_id)
      address = existing_wallet.address
      wallet_name = existing_wallet.label
      encrypted_private_key = str(existing_wallet.encrypted_key[1:])
      text = (
        "Deleting wallet, please save your private key!\n"
        f"{self.cipher.decrypt_wallet(encrypted_private_key)}"
      )
      keyboard = [
        [
          InlineKeyboardButton("⬅️ Go Back", callback_data=str(MAIN_MENU)),
        ]
      ]
      reply_markup = InlineKeyboardMarkup(keyboard)
      await update.message.reply_text(text=text, reply_markup=reply_markup)
            
      self.wallet_interface.delete_wallet(user_id=user_id)
      address, pk_tuple = self.cipher.create_wallet()
      encrypted_private_key = pk_tuple[0]
      self.wallet_interface.create_if_not_exists(
        user_id=user_id,
        address=address,
        label=wallet_name,
        encrypted_key=str(encrypted_private_key)
      )
            
    text = (
      f"Wallet generated successfully!\n"
      f"Name: {wallet_name}\n"
      f"Address: {address}\n"
      f"Private Key: {self.cipher.decrypt_wallet(encrypted_private_key)}"
    )
    
    keyboard = self.get_wallet_keyboard(user_id)
    keyboard_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text=text, reply_markup=keyboard_markup)
    
    logger.info(f"Wallet generated successfully by {user_id}!")
    
    return WALLET_ROUTES
  
  async def fund_wallet_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    context.user_data['operation'] = 'fund'
    text = "Please enter the address you want to fund."
    await query.message.reply_text(text=text, reply_markup=ForceReply())
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
    
    url = "https://faucet-api.ambrosus-test.io/sendto/" + checksum_address

    try:
      async with self.wallet_semaphore:
        async with timeout(600):
          async with ClientSession() as session:
            async with session.get(url, ssl=self.sslcontext) as response:
              logger.info(f"Funding Wallet: {address}")
              text = f"Wallet funded successfully! Check your balance."
              
    except Exception as e:
      await update.message.reply_text(f"Error funding wallet: {str(e)}")
      logger.error(f"Error funding wallet {str(e)}")
      text = "Error funding wallet. Please try again later."
    
    keyboard = self.get_wallet_keyboard(user_id)
    keyboard_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text=text, reply_markup=keyboard_markup)
    
    logger.info(f"User {user_id} is funding {address}.")
    return WALLET_ROUTES
  
  async def get_private_key(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.callback_query.from_user.id
    wallet = self.wallet_interface.fetch_wallet_data(user_id=user_id)
    if wallet:
      warning_text = (
      """
        Are you sure you want to export your Private Key?

        🚨 WARNING: Never share your private key! 🚨
        If anyone, including team or mods, is asking for your private key, IT IS A SCAM! Sending it to them will give them full control over your wallet.

        Tteam and mods will NEVER ask for your private key.
      """ 
      )
      text = (
        f"Private Key: {self.cipher.decrypt_wallet(wallet.encrypted_key[1:])}"
      )
      await update.callback_query.message.reply_text(text=warning_text)
      keyboard = self.get_wallet_keyboard(user_id)
      keyboard_markup = InlineKeyboardMarkup(keyboard)
      await update.callback_query.message.reply_text(text=text, reply_markup=keyboard_markup)
    else:
      text = "No wallet found!"
      await update.callback_query.message.reply_text(text=text)
    return WALLET_ROUTES

  def get_handler(self):
    wallet_routes = [
      MessageHandler(filters.TEXT & filters.REPLY, self.handle_wallet_operation),
      CallbackQueryHandler(self.wallet_management, pattern=f"^{WALLET_MANAGEMENT}$"),
      CallbackQueryHandler(self.gen_wallet_help, pattern=f"^{GEN_WALLET}$",),
      CallbackQueryHandler(self.fund_wallet_help, pattern=f"^{FUND_WALLET}$",),
      CallbackQueryHandler(self.get_private_key, pattern=f"^{PRIVATE_KEY}$"),
      CallbackQueryHandler(self.main_menu, pattern=f"^{MAIN_MENU}$"),
    ]
    wallet_routes.extend(self.airdao_handler.base_commands())
    return wallet_routes