# Documentation

## Introduction

Duckbot is a Telegram Bot Prediction Market implemented with an Orderbook and AMM. Positions are tracked and settled onchain while Orderbook Data & Matching and AMM logic are handled offchain. The smart contracts are written in Solidity and deployed on AirDAO.

Currently, the outcomes are verified solely by a centralized Oracle, managed by the Duck Bot team. The outcomes reported by the Oracle are open for disputes from anyone for 2 days (3 mins in development), which the team will subsequently resolve the dispute. The dispute period is fixed and will not be extended in the case of a dispute.

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


