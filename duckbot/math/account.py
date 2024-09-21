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