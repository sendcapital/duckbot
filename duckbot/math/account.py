from typing import Self
from dataclasses import dataclass

from .types import *
from .position import Position


@dataclass
class Account:
    position: Position
    balance: Notional = 0

    def swap(self, matched_position: Position) -> Position:
        self.position.size -= matched_position.size
        self.position.notional -= matched_position.notional
        return self.position

    def worst_pnl(self) -> Notional:
        if self.position.size > 0:
            worst_exit_notional = 0
        else:
            worst_exit_notional = self.position.max_price * self.position.size
        return worst_exit_notional - self.position.notional

    def available_margin(self) -> Notional:
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