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
  def __init__(self, airdao_handler, config, w3, cipher, db):
    self.config = config
    self.w3: Web3.HTTPProvider = Web3(Web3.HTTPProvider(self.config["airdao_test_rpc"]))
    self.airdao_handler = airdao_handler
    self.db = db
    self.wallet_interface = self.db.wallet_interface
    self.cipher = cipher
    self.main_menu = self.airdao_handler.main_menu_routes.get_main_menu()
    
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
    text = "Please enter the address you want to send funds to in the format: <address> <amount>"
    await query.message.reply_text(text=text, reply_markup=ForceReply())
    logger.info(f"User {user_id} is funding a wallet")
    return TRADE_ROUTES
  
  async def send_funds(self, update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    try:
      wallet = self.wallet_interface.fetch_wallet_data(user_id=user_id)
      address = wallet.address
      encrypted_key = wallet.encrypted_key[1:]
      pk = self.cipher.decrypt(encrypted_key)
      
      message = update.message.text.split(" ")
      if len(message) == 0:
        text = "Invalid command format"
        await update.message.reply_text(text=text)
        return TRADE_ROUTES
      
      receiver_address = message[0].lower()
      amount = float(message[1])
      
      if amount < 5:
        text = "Minimum amount is 5"
        await update.message.reply_text(text=text)
        return TRADE_ROUTES
      
      checksum_receiver_address = self.w3.to_checksum_address(receiver_address)
      checksum_address = self.w3.to_checksum_address(address)
      acct2 = self.w3.eth.account.from_key(pk)
      
      gas_limit = self.w3.eth.estimate_gas({
        'from': checksum_address,
        'to': checksum_receiver_address
      })
      
      transaction = {
        'from': acct2.address,
        'to': checksum_receiver_address,
        'value': self.w3.to_wei(amount, 'ether'),
        'nonce': self.w3.eth.get_transaction_count(checksum_address),
        'gas': gas_limit,
        'gasPrice': self.w3.eth.gas_price,
        'chainId': self.w3.eth.chain_id
      }
      signed = self.w3.eth.account.sign_transaction(transaction, pk)

      tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
      tx = self.w3.eth.get_transaction(tx_hash)    
      text = (
        f"Transaction sent to {receiver_address} for {amount} AMB\n"
        f"Transaction hash: {tx_hash.hex()}"
      )

      keyboard = self.get_trade_keyboard()
      keyboard_markup = InlineKeyboardMarkup(keyboard)
      await update.message.reply_text(text=text, reply_markup=keyboard_markup)
      logger.info(f"User {user_id} is funding {address}.")
      return TRADE_ROUTES 
    except Exception as e:
      logger.error(f"Error sending funds: {e}")
      text = "Error sending funds"
      await update.message.reply_text(text=text)
      return TRADE_ROUTES
    

  def get_handler(self):
    trade_routes = [
      MessageHandler(filters.TEXT & filters.REPLY, self.handle_trade_operation),
      CallbackQueryHandler(self.trade_management, pattern=f"^{TRADE_MANAGEMENT}$"),
      CallbackQueryHandler(self.send_funds_help, pattern=f"^{SEND_FUNDS}$",),
      CallbackQueryHandler(self.main_menu, pattern=f"^{MAIN_MENU}$"),
    ]
    trade_routes.extend(self.airdao_handler.base_commands())
    return trade_routes