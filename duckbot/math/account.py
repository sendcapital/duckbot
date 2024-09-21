from typing import Self
from dataclasses import dataclass

from .types import *
from .position import Position


@dataclass
class Account:
    position: Position

    def swap(self, ...) -> Position:
        self.position.size += ...
        self.position.notional += ...
        return self.position