from web3 import Web3
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ForceReply, Chat
from telegram.ext import (
  CallbackQueryHandler,
  ContextTypes,
  filters,
  MessageHandler,
  CallbackContext,
)
from typing import List

from market import OrderBook, Account, Position
from database import AirDaoDB
from consts import (
  PREDICTION_ROUTES,
  MAIN_MENU,
  PREDICTION_MANAGEMENT,
  MARKET_MAKER_TG_ID
)
from models import (
  Market,
  Wallet
)
from models import Position as PositionModel
from utils import (
  init_logger,
  fetch_eth_balance
)

logger = init_logger(__name__)

class Prediction:
  def __init__(self, airdao_handler, config, cipher, db):
    self.config = config
    self.w3: Web3.HTTPProvider = Web3(Web3.HTTPProvider(self.config["airdao_test_rpc"]))
    self.airdao_handler = airdao_handler
    self.db: AirDaoDB = db
    self.wallet_interface: Wallet = self.db.wallet_interface
    self.market_interface: Market = self.db.market_interface
    self.position_interface: PositionModel = self.db.position_interface
    
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
        InlineKeyboardButton("💰 Claim Settlement", callback_data="claim_settlement"),
      ],
      [
        InlineKeyboardButton("⬅️ Go Back", callback_data=str(MAIN_MENU)),
      ]
    ]
    return keyboard
  
  async def prediction_management(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = ("🔮 What will you predict today? You can predict on sports, elections, crypto prices, and more.\n" +
            "Ready to make your first prediction?")
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
  
  async def claim_settlement(self, update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    
    # check if position exists assume 1 position in db
    positions_data = self.position_interface.fetch_positions(telegram_user_id=query.from_user.id)
    
    if positions_data:
      account = Account(
        Position(positions_data[0].size, positions_data[0].notional),
        balance=0
      )
      
      text = (
        f"🔮 Settlement claimed!\n"
        f"Your wallet balance is now {account.balance} AMB\n"
      )
      keyboard = [
        [
          InlineKeyboardButton("🔮 Make Another Prediction", callback_data=str(PREDICTION_MANAGEMENT)),
          InlineKeyboardButton("⬅️ Go Back", callback_data=str(MAIN_MENU)),
        ]
      ]
      reply_markup = InlineKeyboardMarkup(keyboard)
      await query.message.reply_text(text=text, reply_markup=reply_markup)
    else:
      text = "You have no settlement to claim!"
      keyboard = [
        [
          InlineKeyboardButton("⬅️ Go Back", callback_data=str(PREDICTION_MANAGEMENT)),
        ]
      ]
      reply_markup = InlineKeyboardMarkup(keyboard)
      await query.message.reply_text(text=text, reply_markup=reply_markup)
    
    return PREDICTION_ROUTES
    
  
  async def predict_market(self, update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    if query.data.startswith("category_"):
      category = str(query.data.split("_")[-1]) 
      
      if category == "politics":
        text = f"📈 {category} Category\n" + "Adjust the size of your order as a percentage of your available margin"
        
        markets: List[Market] = self.market_interface.fetch_market_category(category=category)[0]
        
        existing_wallet = self.wallet_interface.fetch_wallet_bool(user_id=query.from_user.id)
        
        if existing_wallet:
          keyboard = []
          for market in markets:
            market_name = ' '.join(market.market_name.split("_"))
            keyboard.append([InlineKeyboardButton(market_name, callback_data=f"select_market_{market.market_id}")])
          keyboard.append([InlineKeyboardButton("⬅️ Go Back", callback_data=str(PREDICTION_MANAGEMENT))])
          reply_markup = InlineKeyboardMarkup(keyboard)
          text = (
            "🔮 Select a market to make your prediction!\n"
          )
          await query.message.reply_text(text=text, reply_markup=reply_markup, parse_mode="HTML")
        else:
          text = "You need to have a wallet to make a prediction!"
          keyboard = [  
            [
              InlineKeyboardButton("Create Wallet", callback_data="create_wallet"),
              InlineKeyboardButton("⬅️ Go Back", callback_data=str(PREDICTION_MANAGEMENT)),
            ]
          ]            
          await query.message.reply_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
          
      else:
        text = "Coming soon!"
        keyboard = [
          [
            InlineKeyboardButton("⬅️ Go Back", callback_data=str(PREDICTION_MANAGEMENT)),
          ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(text=text, reply_markup=reply_markup)
      
    return PREDICTION_ROUTES
  
  async def adjust_size(self, update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("adjust_size_"):
      size = int(query.data.split("_")[-1])
      context.user_data['size'] = size
      text = f"Size adjusted to {size}% of available margin"

      await query.message.reply_text(text=text)
      
      await self.make_prediction(update, context)
      
    else:
      keyboard = [
        [
          InlineKeyboardButton("⬅️ Go Back", callback_data=str(PREDICTION_MANAGEMENT)),
        ]
      ]
      reply_markup = InlineKeyboardMarkup(keyboard)
      await query.message.reply_text(text="Invalid size selection!", reply_markup=reply_markup)
    
    return PREDICTION_ROUTES
  
  async def withdraw_funds(self, update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    
    # TODO: call function to withdraw funds from the contract which handles settlement
    # check for funds in the contract for particular user
    
    # if funds exist:
    funds_exist = False
    
    if funds_exist:
      text = "Funds withdrawn successfully!"
      keyboard = [
        [
          InlineKeyboardButton("⬅️ Go Back", callback_data=str(PREDICTION_MANAGEMENT)),
        ]
      ]
      reply_markup = InlineKeyboardMarkup(keyboard)
      await query.message.reply_text(text=text, reply_markup=reply_markup)
    
    else:
      text = "You have no funds to withdraw!"
      keyboard = [
        [
          InlineKeyboardButton("⬅️ Go Back", callback_data=str(PREDICTION_MANAGEMENT)),
        ]
      ]
      reply_markup = InlineKeyboardMarkup(keyboard)
      await query.message.reply_text(text=text, reply_markup=reply_markup)
    
    return PREDICTION_ROUTES
  
  async def make_prediction(self, update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("select_market_") or query.data.startswith("adjust_size_"):
      market_id = context.user_data.get('market_id', str(query.data.split("_")[-1])) 
      context.user_data['market_id'] = market_id
      
      market_data: Market = self.market_interface.fetch_market_data(market_id=market_id)[0]
      book = OrderBook(
        book = market_data.book,
        price_tick = market_data.price_tick,
        ask_index=market_data.ask_index
      )
            
      # keyboard to adjust size of order in percentage of available margin
      wallet_data = self.wallet_interface.fetch_wallet_data(user_id=query.from_user.id)
      wallet_balance = fetch_eth_balance(self.w3, wallet_data.address)
      
      # check if position exists assume 1 position in db
      positions_data = self.position_interface.fetch_positions(telegram_user_id=query.from_user.id)
        
      if positions_data:
        
        account = Account(
          Position(positions_data[0].size, positions_data[0].notional),
          balance=wallet_balance
        )
      else:
        account = Account(
          Position(0, 0),
          balance=wallet_balance
        )
      
      available_margin = account.available_margin()
      shortened_address = wallet_data.address[:6] + "..." + wallet_data.address[-4:]
      size = context.user_data.get('size', 0)

      text = (
        f"<b>Wallet Info:</b>\n"
        f"Address: {shortened_address}\n"
        f"Current wallet balance: {wallet_balance} AMB\n"
        f"Available Margin: {available_margin} AMB\n"
        f"Default Size: {context.user_data.get('size', 0)} AMB\n"
      )
      
      orderbook_text =  (
        "🔮 Make your prediction!\n\n" +
        "📊 Category: " + market_data.category + "\n"
        "📈 Market: " + ' '.join(market_data.market_name.split('_')) + "\n"
        "📅 Created At: " + str(market_data.created_at) + "\n\n"
        
        f"```{book.pretty()}```"
      )
      
      bid_index = book.price_tick - book.ask_index
      
      keyboard = [
        [
          InlineKeyboardButton(f"🟢 Yes {bid_index}/{book.price_tick - bid_index}", callback_data=f"predict_{market_id}_yes"),
          InlineKeyboardButton(f"🔴 No {book.ask_index}/{book.price_tick - book.ask_index}", callback_data=f"predict_{market_id}_no"),
        ],
        [
          InlineKeyboardButton("👟 Select Size Below", callback_data="None"),
        ],
        [
          InlineKeyboardButton("🟢 25 AMB" if size == 25 else "25 AMB", callback_data="adjust_size_25"),
          InlineKeyboardButton("🟢 50 AMB" if size == 50 else "50 AMB", callback_data="adjust_size_50"),
          InlineKeyboardButton("🟢 75 AMB" if size == 75 else "75 AMB", callback_data="adjust_size_75"),
          InlineKeyboardButton("🟢 100 AMB" if size == 100 else "100 AMB", callback_data="adjust_size_100"),
        ],
        [
          InlineKeyboardButton("🏧 Withdraw Funds", callback_data="withdraw_funds"),
        ],
        [
          InlineKeyboardButton("⬅️ Go Back", callback_data=str(PREDICTION_MANAGEMENT)),
        ]
      ]
      reply_markup = InlineKeyboardMarkup(keyboard)
      await query.message.reply_text(text=text, parse_mode="HTML")
      await query.message.reply_text(text=orderbook_text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
      await query.message.reply_text(text="Invalid market selection!")
    
    return PREDICTION_ROUTES
  
  async def confirm_prediction(self, update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("predict_"):
      market_id, prediction = query.data.split("_")[1:]
      market_data: Market = self.market_interface.fetch_market_data(market_id=market_id)[0]
      book = OrderBook(
        book = market_data.book,
        price_tick = market_data.price_tick,
        ask_index=market_data.ask_index
      )
      positions_data = self.position_interface.fetch_positions(telegram_user_id=query.from_user.id)
      wallet_data = self.wallet_interface.fetch_wallet_data(user_id=query.from_user.id)
      wallet_balance = fetch_eth_balance(self.w3, wallet_data.address)
      
      if wallet_balance > 0:
        if positions_data:
          
          account = Account(
            Position(positions_data[0].size, positions_data[0].notional),
            balance=wallet_balance
          )
        else:
          account = Account(
            Position(0, 0),
            balance=wallet_balance
          )
      
        available_margin = account.available_margin()
        bid_index = book.price_tick - book.ask_index
        size = context.user_data.get('size', 0)
    
        orderbook_text =  (
          f"Your Selection: {"Yes" if prediction == "yes" else "No"}\n"
          f"📊 Category: {market_data.category}\n"
          f"📈 Market: {' '.join(market_data.market_name.split('_'))}\n"
          f"📅 Created At: {str(market_data.created_at)}\n\n"
          
          f"```{book.pretty()}```\n\n"
          
          f"Available Margin: {available_margin}\n"
          f"Size: {size}% of available margin\n"
          f"Payoff: {(1-(bid_index/book.price_tick))*size} AMB\n\n"
          
          f"Please confirm your prediction\n"
          f"Order valid for 30 seconds before auto cancellation\n"
        )      
        keyboard = [
          [
            InlineKeyboardButton("🟢 Confirm", callback_data=f"confirm_{market_id}_{prediction}"),
            InlineKeyboardButton("🔴 Cancel", callback_data=str(PREDICTION_MANAGEMENT)),
          ],
          [
            InlineKeyboardButton("⬅️ Go Back", callback_data=str(PREDICTION_MANAGEMENT)),
          ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(text=orderbook_text, reply_markup=reply_markup, parse_mode="Markdown")
      else:
        text = "Please top up your wallet with funds!"
        keyboard = [  
          [
            InlineKeyboardButton("⬅️ Go Back", callback_data=str(PREDICTION_MANAGEMENT)),
          ]
        ]            
        await query.message.reply_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
      await query.message.reply_text(text="Invalid market selection!")
    
    return PREDICTION_ROUTES
  
  async def predict(self, update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("confirm_"):
      market_id, prediction = query.data.split("_")[1:] # where prediction is 1 or 0 (truthy or falsey)
      
      # TODO: call function to send bid on chain
      
      
      # match accounts for book and decide how much funds to transfer to the vault
      # initiate order book
      market_data: Market = self.market_interface.fetch_market_data(market_id=market_id)[0]
      book = OrderBook(
        book = market_data.book,
        price_tick = market_data.price_tick,
        ask_index=market_data.ask_index
      )
      # initiate market maker and taker account objects
      wallet_data = self.wallet_interface.fetch_wallet_data(user_id=query.from_user.id)
      wallet_balance = fetch_eth_balance(self.w3, wallet_data.address)
      
      if wallet_balance > 0:
        account = Account(
          Position(0, 0),
          balance=wallet_balance
        )
        positions_data = self.position_interface.fetch_positions(telegram_user_id=query.from_user.id)
        if positions_data:
          account = Account(
            Position(positions_data[0].size, positions_data[0].notional),
            balance=wallet_balance
          )
      market_maker = Account(Position(), 100000)

      taker_price = book.price(book.ask_index)
      taker_size = context.user_data.get('size', 0)
      
      # match accounts for market maker and account
      book.match_accounts(market_maker, account, taker_price, taker_size)
      
      # TODO: carry out transaction for market maker and account on-chain
      
      # TODO: query the nonce from the contract
      
      # update position in db for account
      if positions_data:
        self.position_interface.update_position(
          telegram_user_id=query.from_user.id,
          size=account.position.size,
          notional=account.position.notional
        )
      else:
        self.position_interface.create_position(
          telegram_user_id=query.from_user.id,
          size=account.position.size,
          notional=account.position.notional
        )
      
      # update position in db for market_maker after checking for market maker position data
      market_maker_positions_data = self.position_interface.fetch_positions(telegram_user_id=MARKET_MAKER_TG_ID)
      if market_maker_positions_data:
        market_maker.position.size = market_maker_positions_data[0].size
        market_maker.position.notional = market_maker_positions_data[0].notional
        self.position_interface.update_position(
          telegram_user_id=MARKET_MAKER_TG_ID,
          size=market_maker.position.size,
          notional=market_maker.position.notional
        )
      else:
        self.position_interface.create_position(
          telegram_user_id=MARKET_MAKER_TG_ID,
          size=market_maker.position.size,
          notional=market_maker.position.notional
        )
        
      text = (
        f"🔮 Prediction confirmed!\n"
        f"📊 Category: {market_data.category}\n"
        f"📈 Market: {' '.join(market_data.market_name.split('_'))}\n"
        f"📅 Created At: {str(market_data.created_at)}\n\n"
        
        f"Your Selection: {'Yes' if prediction == 'yes' else 'No'}\n"
        f"Size: {taker_size}% of available margin\n"
        f"Payoff: {(1-(book.price(book.ask_index)/book.price_tick))*taker_size} AMB\n\n"
        
        f"Transaction successful!\n"
        f"Your wallet balance is now {account.balance} AMB\n"
      )
      keyboard = [
        [
          InlineKeyboardButton("🔮 Make Another Prediction", callback_data=str(PREDICTION_MANAGEMENT)),
          InlineKeyboardButton("⬅️ Go Back", callback_data=str(MAIN_MENU)),
        ]
      ]
      reply_markup = InlineKeyboardMarkup(keyboard)
      await query.message.reply_text(text=text, reply_markup=reply_markup)
    else:
      await query.message.reply_text(text="Invalid market selection!")
      
    return PREDICTION_ROUTES
         

  def get_handler(self):
    prediction_routes = [
      MessageHandler(filters.TEXT & filters.REPLY, self.handle_prediction_operation),
      CallbackQueryHandler(self.prediction_management, pattern=f"^{PREDICTION_MANAGEMENT}$"),
      CallbackQueryHandler(self.claim_settlement, pattern=f"claim_settlement"),
      CallbackQueryHandler(self.predict_market, pattern=f"^category_.+$"),
      CallbackQueryHandler(self.make_prediction, pattern=f"^select_market_.+$"),
      CallbackQueryHandler(self.adjust_size, pattern=f"^adjust_size_.+$"),
      CallbackQueryHandler(self.confirm_prediction, pattern=f"^predict_.+$"),
      CallbackQueryHandler(self.withdraw_funds, pattern=f"withdraw_funds"),
      CallbackQueryHandler(self.predict, pattern=f"^confirm_.+$"),
      CallbackQueryHandler(self.main_menu, pattern=f"^{MAIN_MENU}$"),
    ]
    prediction_routes.extend(self.airdao_handler.base_commands())
    return prediction_routes