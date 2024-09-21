from typing import Self
from dataclasses import dataclass

from .types import *


@dataclass
class Position:
    size: Size = 0
    notional: Notional = 0

    def from_price(cls: Self, price: Price, size: Size) -> Self:
        return cls(size=size, notional=price * size)
    
    def price(self) -> float:
        return self.notional / self.size if self.size else 0

