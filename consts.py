from telegram.ext import (
  ConversationHandler,
)
END = ConversationHandler.END

# Stages
QUERY_ROUTES, EXPLORER_ROUTES, WALLET_ROUTES, TRADE_ROUTES, END_ROUTES = range(5)

(
  MAIN_MENU,
  TRADE_MANAGEMENT,
  WALLET_MANAGEMENT,
  EXPLORER_MANAGEMENT,
  TRADE_MANAGEMENT,
  NETWORK_INFO,
  BALANCE,
  ERC20BALANCE,
  GEN_WALLET,
  FUND_WALLET,
  SEND_FUNDS,
  FETCH_BRIDGE_INFO
) = range(12)





