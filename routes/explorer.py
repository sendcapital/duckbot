#!/usr/bin/env python
# -*- coding: utf-8 -*-
from web3 import Web3
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ForceReply
from telegram.ext import (
  ContextTypes,
  CallbackContext,
  filters,
  MessageHandler,
  CallbackQueryHandler,
  CommandHandler
)
from consts import (
  EXPLORER_ROUTES,
  MAIN_MENU,
  BALANCE,
  NETWORK_INFO,
  ERC20BALANCE,
  EXPLORER_MANAGEMENT
)
from utils import (
  init_logger
)

logger = init_logger(__name__)

class Explorer:
  def __init__(self, airdao_handler , config, w3):
    self.airdao_handler = airdao_handler
    self.config = config
    self.main_menu = self.airdao_handler.main_menu_routes.get_main_menu()
    self.w3 = w3

  def get_explorer_keyboard(self):
    keyboard = [
      [
        InlineKeyboardButton("⭐ Fetch AMB Balance", callback_data=str(ERC20BALANCE)),
        InlineKeyboardButton("💵 Fetch Balance", callback_data=str(BALANCE)),
      ],
      [
        InlineKeyboardButton("🔍 Check Network Info", callback_data=str(NETWORK_INFO)),
      ],
      [
        InlineKeyboardButton("⬅️ Go Back", callback_data=str(MAIN_MENU)),
      ]
    ]
    return keyboard
  
  async def explorer_management(self, update: Update,  context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.callback_query:
      user_id = update.callback_query.from_user.id
      query = update.callback_query
      await query.answer()
    if update.message:
      user_id = update.message.from_user.id
    
    text = ("AirDao Explorer is up and running! What do you want to search for?")
    keyboard = self.get_explorer_keyboard()
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
      await update.message.reply_text(text=text, reply_markup=reply_markup)
      
    elif update.callback_query:
      query = update.callback_query
      await query.message.edit_text(text=text, reply_markup=reply_markup)
    return EXPLORER_ROUTES
  
  async def handle_explorer_operation(self, update: Update, context: CallbackContext):
    operation = context.user_data.get('operation')
    if operation == 'balance':
      await self.fetch_eth_balance(update, context)
    if operation == 'erc20balance':
      await self.fetch_AMB_balance(update, context)
    return EXPLORER_ROUTES


  async def fetch_eth_balance_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    text = (
      "Type an address to fetch their balance\n"
      "\n"
      "Example:\n"
      "\n"
      "0xC99Cdcd2F59eF3908fD53d88d8de24482F898d37"
    )
    context.user_data['operation'] = 'balance'
    await query.message.edit_text(text="Return back to Main Menu")
    await query.message.reply_text(text=text, reply_markup=ForceReply(selective=True))
    return EXPLORER_ROUTES
  
  async def fetch_eth_balance(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    message = update.message.text.split(" ")
    if len(message) == 0:
      text = "Invalid command format"
      await update.message.reply_text(text=text)
      return EXPLORER_ROUTES
    
    address = message[0].lower()
    checksum_address = self.w3.to_checksum_address(address)
    try:
      balance = self.w3.eth.get_balance(checksum_address)
      formatted_balance = self.w3.from_wei(balance, 'ether')
      keyboard = self.get_explorer_keyboard()
      keyboard_markup = InlineKeyboardMarkup(keyboard)
      await update.message.reply_text(f"The balance of {message[0]} is {formatted_balance} AMB", reply_markup=keyboard_markup)
      logger.info(f"Successful fetching of balance for {address}")
    except Exception as e:
      logger.error(f"Error fetching balance: {str(e)}")
      await update.message.reply_text(f"Error fetching balance: {str(e)}")
    return EXPLORER_ROUTES
  
  async def fetch_erc20_balance_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    text = (
      "Type an address and token contract address to fetch their ERC20 balance\n"
      "\n"
      "Example:\n"
      "\n"
      "0xC99Cdcd2F59eF3908fD53d88d8de24482F898d37"
    )
    context.user_data['operation'] = 'erc20balance'
    await query.message.reply_text(text=text, reply_markup=ForceReply(selective=True))
    return EXPLORER_ROUTES
  
  async def fetch_AMB_balance(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    message = update.message.text.split(" ")
    if len(message) == 0:
      text = "Invalid command format"
      await update.message.reply_text(text=text)
      return EXPLORER_ROUTES
    
    address = message[0].lower()
    token_contact_address = "0x096B5914C95C34Df19500DAff77470C845EC749D" #TODO: What is the airdao token contract address?
    checksum_address = self.w3.to_checksum_address(address)
    checksum_token_address = self.w3.to_checksum_address(token_contact_address)
    
    erc20_abi = [
      {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"},
      {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "decimals", "type": "uint8"}], "type": "function"}
    ]
    try:
      contract = self.w3.eth.contract(address=self.w3.to_checksum_address(checksum_token_address), abi=erc20_abi)
      balance = contract.functions.balanceOf(self.w3.to_checksum_address(checksum_address)).call()
      print(balance)
      decimals = contract.functions.decimals().call()
      formatted_balance = balance / (10 ** decimals)
      keyboard = [[InlineKeyboardButton("⬅️ Go Back", callback_data=str(EXPLORER_MANAGEMENT))]]
      keyboard_markup = InlineKeyboardMarkup(keyboard)
      await update.message.reply_text(f"The ERC20 token balance of {message[0]} is {formatted_balance}", reply_markup=keyboard_markup)
      logger.info(f"Successful fetching of ERC20 balance for {address}")
    except Exception as e:
      await update.message.reply_text(f"Error fetching ERC20 balance: {str(e)}")
      logger.error(f"Error fetching ERC20 balance: {str(e)}")
    return EXPLORER_ROUTES

  async def network_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    try:
      network_id = self.w3.net.version
      latest_block = self.w3.eth.block_number
      gas_price = self.w3.eth.gas_price
      logger.info("Fetching network info")
      await query.message.reply_text(f"🔗 AirDAO\n\n- Network ID: {network_id}\n- Latest Block: {latest_block}\n- Current Gas Price: {self.w3.from_wei(gas_price, 'gwei')} Gwei")
    except Exception as e:
      await query.message.reply_text(f"Error fetching network info: {str(e)}")
      logger.error(f"Error fetching network info: {str(e)}")
    return EXPLORER_ROUTES

  
  
  def get_handler(self):
    explorer_routes = [
      MessageHandler(filters.TEXT & filters.REPLY, self.handle_explorer_operation),
      CallbackQueryHandler(self.network_info, pattern=f"^{NETWORK_INFO}$"),
      CallbackQueryHandler(self.fetch_eth_balance_help, pattern=f"^{BALANCE}$"),
      CallbackQueryHandler(self.fetch_erc20_balance_help, pattern=f"^{ERC20BALANCE}$"),
      CallbackQueryHandler(self.main_menu, pattern=f"^{MAIN_MENU}$"),
    ]
    explorer_routes.extend(self.airdao_handler.base_commands())
    return explorer_routes