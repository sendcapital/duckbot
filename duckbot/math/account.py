from typing import Self
from dataclasses import dataclass

from .types import *
from .position import Position


@dataclass
class Account:
    position: Position

    def swap(self, matched_position: Position) -> Position:
        self.position.size -= matched_position.size
        self.position.notional -= matched_position.notional
        return self.position

    def settle(self) -> Notional:
        # settle account if they have closed all positions
        if self.position.size == 0:
            pnl = -self.position.notional
            self.position.notional = 0
            return pnl
        else:
            return 0
