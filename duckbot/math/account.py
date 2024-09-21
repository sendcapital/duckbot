from typing import Self
from dataclasses import dataclass

from .types import *
from .position import Position


@dataclass
class Account:
    position: Position
    balance: Notional = 0

    def _swap(self, matched_position: Position) -> Position:
        self.position.size -= matched_position.size
        self.position.notional -= matched_position.notional
        return self.position

    def worst_pnl(self) -> Notional:
        # worst possible realised pnl
        if self.position.size > 0:
            worst_exit_notional = 0
        else:
            worst_exit_notional = self.position.max_price * self.position.size
        return worst_exit_notional - self.position.notional

    def available_margin(self) -> Notional:
        # notional available to be used to perform new swaps. Check this before accepting a swap
        return self.balance + self.worst_pnl()

    def settle(self) -> Notional:
        # settle account if they have margin
        available = self.available_margin()
        if available > 0:
            self.position.notional += available
            self.balance -= available
            return available
        else:
            return 0