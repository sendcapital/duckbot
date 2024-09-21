from typing import Self
from dataclasses import dataclass

Price = int
Notional = Price
Size = int

@dataclass
class OrderBook:
    book: list[Size]
    price_tick: Price
    index: int

    def __post_init__(self: Self):
        self.len_book: int = len(self.book)

    def pretty(self: Self) -> str:
        l_ask = (f'{self.price(i):5}% | {-self.size(i):5}' for i in range(self.len_book - 1, self.index - 1, -1))
        l_bid = (f'{self.price(i):5}% | {self.size(i):5}' for i in range(self.index - 1, -1, -1))
        return f'{'\n'.join(l_ask)}\n{'-' * 15}\n price |  size\n{'-' * 15}\n{'\n'.join(l_bid)}'
    
    def price(self: Self, index: int) -> Price:
        return self.price_tick * (index + 1)

    def size(self: Self, index: int) -> Size:
        return self.book[index] if 0 <= index < self.len_book else 0

    def best_index(self: Self, is_bid: bool) -> int:
        return self.index - 1 if is_bid else self.index

    def best_order(self: Self, is_bid: bool) -> (Price, Size):
        index = self.best_index(is_bid)
        return self.price(index), self.size(index)

    # mutates
    def match(self: Self, taker_price: Price, taker_size: Size) -> (Notional, Size):
        # if taker_size >> maker_size: wipe & continue else: hit & stop
        # taker_size = 3; maker_size = -5 -> -2. stop
        # taker_size = 7; maker_size = -5 -> 2. cont
        
        # maker_size = 2; new_maker_size = -1, 0, 1; c s s; f t t
        # maker_size = 0; new_maker_size = -1, 0, 1; c s c; f t f
        # maker_size = -3; new_maker_size = -2, 0, 2; s s c; t t f

        print(f'taker size: {taker_size}')
        is_bid_maker = taker_size < 0  # maker is bid (opposite of taker)
        maker_price, maker_size = self.best_order(is_bid_maker)
        new_maker_size = maker_size + taker_size  # pending size
        
        if (taker_price != maker_price and is_bid_maker == (maker_price < taker_price)):
            # cease: no more match
            # maker_bid < taker_ask || taker_bid < maker_ask
            print(f'no match: {0} @ {maker_price}')
            return 0, 0
        
        if (maker_size != 0) and ((new_maker_size == 0) or ((maker_size > 0) == (new_maker_size > 0))):
            # stop
            matched_maker_size = -taker_size
            print(f'stop: {taker_size} @ {maker_price}')
            self.book[self.best_index(not is_bid_maker)] -= matched_maker_size
            self.book[self.best_index(is_bid_maker)] -= matched_maker_size
            return maker_price * matched_maker_size, matched_maker_size
        else:
            # cont
            matched_maker_size = self.book[self.best_index(is_bid_maker)]
            print(f'cont: {matched_maker_size} @ {maker_price}')
            self.book[self.best_index(not is_bid_maker)] -= matched_maker_size
            self.book[self.best_index(is_bid_maker)] = 0
            self.index += -1 if is_bid_maker else 1  # fix this
            if 0 < self.index < self.len_book:
                print(self.index)
                next_notional, next_size = self.match(taker_price, taker_size + matched_maker_size)
            else:
                # end of book
                print(f'end: {0} @ {maker_price}')
                self.index = min(max(self.index, 1), self.len_book - 1)
                next_notional, next_size = 0, 0
            return next_notional + maker_price * matched_maker_size, next_size + matched_maker_size
