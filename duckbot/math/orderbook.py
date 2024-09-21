from typing import Self
from dataclasses import dataclass

from .types import *
from .position import Position

import logging

log = logging.getLogger(__name__)

@dataclass
class OrderBook:
    book: list[Size]
    price_tick: Price
    ask_index: int

    def __post_init__(self):
        self.len_book: int = len(self.book)  # fixed length
    
    def price(self, index: int) -> Price:
        return self.price_tick * (index + 1)

    def size(self, index: int) -> Size:
        return self.book[index] if 0 <= index < self.len_book else 0

    def best_index(self, is_bid: bool) -> int:
        return self.ask_index - 1 if is_bid else self.ask_index

    def best_order(self, is_bid: bool) -> (Price, Size):
        index = self.best_index(is_bid)
        return self.price(index), self.size(index)

    # mutates
    # matches limit order against book. ie. input taker price + slippage allowance
    # notional is amount taker pays
    def match(self, taker_price: Price, taker_size: Size) -> Position:
        # if |taker_size| > |maker_size|: wipe & continue else: hit & stop
        # taker_size = 3; maker_size = -5 -> -2. stop
        # taker_size = 7; maker_size = -5 -> 2. cont
        
        # maker_size = 2; pending_maker_size = -1, 0, 1; c s s; f t t
        # maker_size = 0; pending_maker_size = -1, 0, 1; c s c; f t f
        # maker_size = -3; pending_maker_size = -1, 0, 1; s s c; t t f

        is_bid_maker = taker_size < 0  # maker is bid (opposite of taker)
        maker_price, maker_size = self.best_order(is_bid_maker)
        pending_maker_size = maker_size + taker_size  # pending size
        
        if (taker_price != maker_price and is_bid_maker == (maker_price < taker_price)):
            # cease: no more match
            # maker_bid < taker_ask || taker_bid < maker_ask
            return Position()

        is_stop = (maker_size != 0) and ((pending_maker_size == 0) or ((maker_size > 0) == (pending_maker_size > 0)))
        matched_maker_size = -taker_size if is_stop else self.book[self.best_index(is_bid_maker)]
        self.book[self.best_index(not is_bid_maker)] -= matched_maker_size
        self.book[self.best_index(is_bid_maker)] -= matched_maker_size

        if is_stop:
            # stop
            return Position(size=matched_maker_size, notional=maker_price * matched_maker_size)
        else:
            # cont
            self.ask_index += -1 if is_bid_maker else 1
            
            if 0 < self.ask_index < self.len_book:
                next_match = self.match(taker_price, taker_size + matched_maker_size)  # recursion
            else:
                # end of book
                self.ask_index = min(max(self.ask_index, 1), self.len_book - 1)
                next_match = Position()
            return Position(size=next_match.size + matched_maker_size, notional=next_match.notional + maker_price * matched_maker_size)

    def pretty(self) -> str:
        l_ask = (f'{self.price(i):5}% | {-self.size(i):5}' for i in range(self.len_book - 1, self.ask_index - 1, -1))
        l_bid = (f'{self.price(i):5}% | {self.size(i):5}' for i in range(self.ask_index - 1, -1, -1))
        return f'{'\n'.join(l_ask)}\n{'-' * 15}\n price |  size\n{'-' * 15}\n{'\n'.join(l_bid)}'
