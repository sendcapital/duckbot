# Documentation
## Introduction
Duckbot🦆 is a Telegram Bot Prediction Market implemented with an Orderbook and AMM. Positions are tracked and settled onchain while Orderbook Data & Matching and AMM logic are handled offchain. The smart contracts are written in Solidity and deployed on AIRDAO.

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