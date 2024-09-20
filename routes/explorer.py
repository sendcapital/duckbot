#!/usr/bin/env python
# -*- coding: utf-8 -*-
from web3 import Web3
import asyncio
from aiohttp import ClientSession
from async_timeout import timeout
import json
import ssl
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
  EXPLORER_MANAGEMENT,
  FETCH_BRIDGE_INFO
)
from utils import (
  init_logger,
  round_to_first_three_nonzero_digits
)

logger = init_logger(__name__)

class Explorer:
  def __init__(self, airdao_handler , config, w3):
    self.airdao_handler = airdao_handler
    self.config = config
    self.main_menu = self.airdao_handler.main_menu_routes.get_main_menu()
    self.w3: Web3.HTTPProvider = w3
    self.explorer_semaphore = asyncio.Semaphore(64)
    self.sslcontext = ssl.create_default_context()


  def get_explorer_keyboard(self):
    keyboard = [
      [
        InlineKeyboardButton("⭐ Fetch AMB Balance", callback_data=str(ERC20BALANCE)),
        InlineKeyboardButton("💵 Fetch Balance", callback_data=str(BALANCE)),
      ],
      [
        InlineKeyboardButton("🔍 Check Network Info", callback_data=str(NETWORK_INFO)),
        InlineKeyboardButton("🌉 Fetch Bridge Info", callback_data=str(FETCH_BRIDGE_INFO)),
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
      await self.fetch_erc20_balance(update, context)
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
      "0xe10eB55f6EeF66218BbE58B749428ec4A51D6659,SAMB"
    )
    context.user_data['operation'] = 'erc20balance'
    await query.message.reply_text(text=text, reply_markup=ForceReply(selective=True))
    return EXPLORER_ROUTES
  
  async def fetch_erc20_balance(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    message = update.message.text.split(",")
    if len(message) == 0:
      text = "Invalid command format"
      await update.message.reply_text(text=text)
      return EXPLORER_ROUTES
    
    address = message[0].lower()
    symbol = message[1].upper()
    
    # TODO: Temporary - fetch token contract address from token_dict
    token_dict = {
      "SAMB": "0x2b2d892C3fe2b4113dd7aC0D2c1882AF202FB28F",
    }
    
    token_address = token_dict[symbol]
    
    checksum_address = self.w3.to_checksum_address(address)
    checksum_token_address = self.w3.to_checksum_address(token_address)
    
    erc20_abi = [
      {
        "inputs": [
        {
          "internalType": "address",
          "name": "account",
          "type": "address"
        }
        ],
        "name": "balanceOf",
        "outputs": [
        {
          "internalType": "uint256",
          "name": "",
          "type": "uint256"
        }
        ],
        "stateMutability": "view",
        "type": "function"
      },
      {
        "inputs": [],
        "name": "decimals",
        "outputs": [
        {
          "internalType": "uint8",
          "name": "",
          "type": "uint8"
        }
        ],
        "stateMutability": "view",
        "type": "function"
      },
    ]
    
    try:
      contract = self.w3.eth.contract(address=self.w3.to_checksum_address(checksum_token_address), abi=erc20_abi)
      balance = contract.functions.balanceOf(checksum_address).call()

      decimals = contract.functions.decimals().call()      
      formatted_balance = balance / (10 ** decimals)
      
      keyboard = [[InlineKeyboardButton("⬅️ Go Back", callback_data=str(EXPLORER_MANAGEMENT))]]
      keyboard_markup = InlineKeyboardMarkup(keyboard)
      await update.message.reply_text(f"The {symbol} token balance of {message[0]} is \n {round_to_first_three_nonzero_digits(formatted_balance)}", reply_markup=keyboard_markup)
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
  
  async def fetch_bridge_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    try:
      async with self.explorer_semaphore:
        async with timeout(600):
          async with ClientSession() as session:
            async with session.get(self.config["bridge_info"], ssl=self.sslcontext) as response:
              logger.info(f"Retrieving bridge info from {self.config["bridge_info"]}")
              result = await response.text()
    except Exception as e:
      await query.message.reply_text(f"Error fetching bridge info: {str(e)}")
      logger.error(f"Error fetching bridge info: {str(e)}")
      
    if result:
      result = json.loads(result)
      networks = result['bridges']
      eth_bridges = networks["eth"]
      amb_eth = eth_bridges["amb"]
      eth_amb = eth_bridges["side"]
      bsc_bridges = networks["bsc"]
      amb_bsc = bsc_bridges["amb"]
      bsc_amb = bsc_bridges["side"]
      samb_contract_address = "0x2b2d892C3fe2b4113dd7aC0D2c1882AF202FB28F"
      
      amb_eth_checksum = self.w3.to_checksum_address(amb_eth)
      amb_eth_balance = self.w3.eth.get_balance(amb_eth_checksum, "latest") 

      amb_bsc_checksum = self.w3.to_checksum_address(amb_bsc)
      amb_bsc_balance = self.w3.eth.get_balance(amb_bsc_checksum, "latest")
      
      erc20_abi = [
        {
          "inputs": [
          {
            "internalType": "address",
            "name": "account",
            "type": "address"
          }
          ],
          "name": "balanceOf",
          "outputs": [
          {
            "internalType": "uint256",
            "name": "",
            "type": "uint256"
          }
          ],
          "stateMutability": "view",
          "type": "function"
        },
      ]
      
      try:
        samb_contract = self.w3.eth.contract(address=self.w3.to_checksum_address(samb_contract_address), abi=erc20_abi)
        amb_eth_balance = samb_contract.functions.balanceOf(self.w3.to_checksum_address(amb_eth)).call()
        amb_bsc_balance = samb_contract.functions.balanceOf(self.w3.to_checksum_address(amb_bsc)).call()
        formatted_amb_eth_balance = self.w3.from_wei(amb_eth_balance, 'ether')
        formatted_amb_bsc_balance = self.w3.from_wei(amb_bsc_balance, 'ether')
        
        shortened_amb_eth_address = amb_eth[:8] + "..." + amb_eth[-5:]
        shortened_amb_bsc_address = amb_bsc[:8] + "..." + amb_bsc[-5:]
        shortened_bsc_amb_address = bsc_amb[:8] + "..." + bsc_amb[-5:]
        shortened_eth_amb_address = eth_amb[:8] + "..." + eth_amb[-5:]

        text = (
          "🌉 Bridge Info\n\n"
          "🟣 Ethereum\n"
          f"🔗 AMB -> ETH: <a href='https://airdao.io/explorer/address/{amb_eth}'>{shortened_amb_eth_address}</a>\n"
          f"💰 Balance: {round_to_first_three_nonzero_digits(formatted_amb_eth_balance)} SAMB\n"
          f"🔗 ETH -> AMB:  <a href='https://etherscan.io/address/{eth_amb}'>{shortened_eth_amb_address}</a>\n\n"
          "🟡 Binance Smart Chain\n"
          f"🔗 AMB -> BSC: <a href='https://airdao.io/explorer/address/{amb_bsc}'>{shortened_amb_bsc_address}</a>\n"
          f"💰 Balance: {round_to_first_three_nonzero_digits(formatted_amb_bsc_balance)} SAMB\n"
          f"🔗 BSC -> AMB: <a href='https://bscscan.com/address/{bsc_amb}'>{shortened_bsc_amb_address}</a>"
        )
        
        keyboard = self.get_explorer_keyboard()
        keyboard_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(text=text, reply_markup=keyboard_markup, parse_mode="HTML")
      except Exception as e:
        await query.message.reply_text(f"Error fetching bridge info: {str(e)}")
        logger.error(f"Error fetching bridge info: {str(e)}")
        
      return EXPLORER_ROUTES
    
  def get_handler(self):
    explorer_routes = [
      MessageHandler(filters.TEXT & filters.REPLY, self.handle_explorer_operation),
      CallbackQueryHandler(self.network_info, pattern=f"^{NETWORK_INFO}$"),
      CallbackQueryHandler(self.fetch_eth_balance_help, pattern=f"^{BALANCE}$"),
      CallbackQueryHandler(self.fetch_erc20_balance_help, pattern=f"^{ERC20BALANCE}$"),
      CallbackQueryHandler(self.fetch_bridge_info, pattern=f"^{FETCH_BRIDGE_INFO}$"),
      CallbackQueryHandler(self.main_menu, pattern=f"^{MAIN_MENU}$"),
    ]
    explorer_routes.extend(self.airdao_handler.base_commands())
    return explorer_routes