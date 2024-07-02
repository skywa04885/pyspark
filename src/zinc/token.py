from __future__ import annotations
from enum import Enum
from dataclasses import dataclass


class ZincTokenType(Enum):
    KEYWORD = 0
    IDENTIFIER = 10
    SYMBOL = 20
    REF = 30
    STR = 40
    DATE = 50
    DATETIME = 60
    TIME = 70
    URI = 80
    NUMBER = 90
    GRID_START = 91
    GRID_END = 92
    BOOL = 93
    LPAREN = 100
    RPAREN = 110
    LBRACKET = 120
    RBRACKET = 130
    LBRACE = 140
    RBRACE = 150
    COLON = 160
    COMMA = 170
    LINEFEED = 180


@dataclass(frozen=True)
class ZincToken:
    t: ZincTokenType
    s: str

    @staticmethod
    def make(t: ZincTokenType, s: str) -> ZincToken:
        return ZincToken(t, s)

    def __len__(self) -> int:
        return len(self.s)

    def __str__(self) -> str:
        return self.s

    def __repr__(self) -> str:
        return f"{self.t} ({self.s})"
