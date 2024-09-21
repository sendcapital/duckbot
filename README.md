# Documentation

## Introduction

Duck Bot is a Telegram Bot Prediction Market implemented with an Orderbook and AMM. Positions are tracked and settled onchain while Orderbook Data & Matching and AMM logic are handled offchain. The smart contracts are written in Solidity and deployed on AirDAO.

Bets are placed and settled in the native token of the chain, AMB.

Aggregation uses perps market design with prices as probabilities ranging from 0% to 100%.

The LP to the AMM is the bot deployer. The AMM is a grid trading strategy with equally spaced orders. There are no trading fees; the AMM earns through the spread.

Users can only place Market Orders via the bot, so the taker will always be the user and the maker will always be the bot deployer.

The outcomes are verified solely by a centralized Oracle, managed by the Duck Bot team via a multisignature. The outcomes reported by the Oracle are open for disputes from anyone for 2 days (3 mins in dev), which the team will subsequently resolve. The dispute period is fixed and will not be extended in the case of a dispute.

## Structure

- Chain
  - Market.Account
    - Balance
    - Positions
    - Deposit / Withdrawal
  - Oracle
- Offchain
  - Orderbook
    - Orders
    - Matching Logic
  - AMM
    - AMM Logic
- UI
  - Telegram Bot
  - Discord trading alerts

## Components

### Chain
Accounts have a Balance and Positions per Prediction Market. A position consists of an aggregated notional and size which is sufficient tracking information.

### Offchain
The orderbook is stored in an offchain PostgreSQL database. The AMM gridbot parameters are fixed, so this results in a fixed list of signed sizes to represent the book.

The matching engine logic is also conducted offchain whenever a user attempts to bet, which then submits the match onchain to complete the trade.

The AMM logic is embedded in the matching engine which replaces filled Asks with Bids one price level lower, and filled Bids with Asks one price level higher.

### UI
Users interact with the Telegram Bot to input their actions, including wallet creation & management, deposit, withdrawal, betting.

There is also a Discord Webhook for Trading Alerts in https://discord.gg/n7uuEhFD.