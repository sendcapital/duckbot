@dataclass
class ABook:
    index: int
    book: list[Size]
    price_tick: Price

    def __post_init__(self: Self):
        self.book_len: int = len(self.book)
    
    def price(self: Self, index: int) -> Price:
        return self.price_tick * index

    def size(self: Self, index: int) -> Size:
        return self.book[index] if 0 <= index < self.book_len else 0

    def best_index(self: Self, is_bid: bool) -> int:
        return self.index - 1 if is_bid else self.index

    def best_order(self: Self, is_bid: bool) -> (Price, Size):
        index = self.best_index(is_bid)
        return self.price(index), self.size(index)

    # mutates
    def match(self: Self, price: Price, size: Size) -> (Notional, Size):
        # if size >> maker_size: wipe & continue else: hit & stop
        # size = 3; maker_size = -5 -> -2. stop
        # size = 7; maker_size = -5 -> 2. cont
        
        # maker_size = 2; new_maker_size = -1, 0, 1; c s s; f t t
        # maker_size = 0; new_maker_size = -1, 0, 1; c s c; f t f
        # maker_size = -3; new_maker_size = -2, 0, 2; s s c; t t f

        is_bid_maker = size < 0  # maker is bid (opposite of taker)
        maker_price, maker_size = self.best_order(is_bid_maker)
        new_maker_size = maker_size + size
        
        if (price != maker_price and is_bid_maker == (maker_price < price)):
            # cease: no more match
            print(f'cease: {0} @ {maker_price}')
            return 0, 0
        
        if (maker_size != 0) and ((new_maker_size == 0) or ((maker_size > 0) == (new_maker_size > 0))):
            # stop
            print(f'stop: {size} @ {maker_price}')
            self.book[self.best_index(not is_bid_maker)] += size
            self.book[self.best_index(is_bid_maker)] += size
            return maker_price * size, size
        else:
            # cont
            match_size = self.book[self.best_index(is_bid_maker)]
            print(f'cont: {match_size} @ {maker_price}')
            self.book[self.best_index(not is_bid_maker)] -= match_size
            self.book[self.best_index(is_bid_maker)] = 0
            self.index += -1 if is_bid_maker else 1
            if 0 < self.index < self.book_len:
                print(self.index)
                next_notional, next_size = self.match(price, size - match_size)
            else:
                # end of book
                print(f'end: {0} @ {maker_price}')
                self.index = min(max(self.index, 1), self.book_len - 1)
                next_notional, next_size = 0, 0
            return maker_price * match_size + next_notional, match_size + next_size
