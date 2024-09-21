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
- Telegram Bot
  - UI
- Discord trading alerts

## Components

### Chain
Accounts have a Balance and Positions per Prediction Market. A position consists of an aggregated notional and size which is sufficient tracking information.