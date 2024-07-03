from __future__ import annotations
from dataclasses import dataclass
from typing import ClassVar, Dict, Final, Iterator, List, Optional
from abc import ABC, abstractmethod
from datetime import date, datetime, time
import math

from zinc.grammer import ZincGrammar


class HVal(ABC):
    @dataclass(frozen=True)
    class InvalidAttributeError(Exception):
        message: str | None


@dataclass(frozen=True)
class HNull(HVal):
    INSTANCE: ClassVar[HNull]

    @staticmethod
    def make() -> HNull:
        return HNull.INSTANCE

    def __eq__(self, other: object, /) -> bool:
        return isinstance(other, HNull)


HNull.INSTANCE = HNull()


@dataclass(frozen=True)
class HMarker(HVal):
    INSTANCE: ClassVar[HMarker]

    @staticmethod
    def make() -> HMarker:
        return HMarker.INSTANCE

    def __eq__(self, other: object, /) -> bool:
        return isinstance(other, HMarker)


HMarker.INSTANCE = HMarker()


@dataclass(frozen=True)
class HRemove(HVal):
    INSTANCE: ClassVar[HRemove]

    @staticmethod
    def make() -> HRemove:
        return HRemove.INSTANCE

    def __eq__(self, other: object, /) -> bool:
        return isinstance(other, HRemove)


HRemove.INSTANCE = HRemove()


@dataclass(frozen=True)
class HNa(HVal):
    INSTANCE: ClassVar[HNa]

    @staticmethod
    def make() -> HNa:
        return HNa.INSTANCE

    def __eq__(self, other: object, /) -> bool:
        return isinstance(other, HNa)


HNa.INSTANCE = HNa()


@dataclass(frozen=True)
class HSymbol(HVal):
    val: str

    @staticmethod
    def make(val: str) -> HSymbol:
        return HSymbol(val)

    def __eq__(self, other: object, /) -> bool:
        return other.val == self.val if isinstance(other, HSymbol) else False


@dataclass(frozen=True)
class HCol(HVal):
    @staticmethod
    def make(index: int, name: str, meta: Dict[str, HVal]) -> HCol:
        return HCol(index, name, meta)

    index: int
    name: str
    meta: Dict[str, HVal]

    def __eq__(self, other: object, /) -> bool:
        if not isinstance(other, HCol):
            return False
        elif other.index != self.index:
            return False
        elif other.name != self.name:
            return False
        elif other.meta != self.meta:
            return False

        return True


@dataclass(frozen=True)
class HRef(HVal):
    val: Final[str]
    name: Final[Optional[HStr]]

    @staticmethod
    def make(val: str, name: Optional[HStr] = None) -> HRef:
        return HRef(val, name)

    def with_name(self, name: HStr) -> HRef:
        return HRef.make(self.val, name)

    def __eq__(self, other: object, /) -> bool:
        return (
            (other.val == self.val and other.name == self.name)
            if isinstance(other, HRef)
            else False
        )


@dataclass(frozen=True)
class HRow(HVal):
    @staticmethod
    def make(cells: List[HVal]) -> HRow:
        return HRow(cells)

    cells: List[HVal]

    def __len__(self) -> int:
        return len(self.cells)

    def __iter__(self) -> Iterator[HVal]:
        return iter(self.cells)

    def __getitem__(self, key: int) -> HVal:
        return self.cells[key]


@dataclass(frozen=True)
class HGrid(HVal):
    @staticmethod
    def make(meta: Dict[str, HVal], cols: List[HCol], rows: List[HRow]) -> HGrid:
        return HGrid(meta, cols, rows)

    meta: Dict[str, HVal]
    cols: List[HCol]
    rows: List[HRow]


@dataclass(frozen=True)
class HDate(HVal):
    val: date

    @staticmethod
    def make(val: date) -> HDate:
        return HDate(val)
    
    def __eq__(self, other: object, /) -> bool:
        return self.val == other.val if isinstance(other, HDate) else False


@dataclass(frozen=True)
class HTime(HVal):
    val: time

    @staticmethod
    def make(val: time) -> HTime:
        return HTime(val)

    def __eq__(self, other: object, /) -> bool:
        return self.val == other.val if isinstance(other, HTime) else False


@dataclass(frozen=True)
class HDateTime(HVal):
    val: datetime

    @staticmethod
    def make(val: datetime) -> HDateTime:
        return HDateTime(val)

    def __eq__(self, other: object, /) -> bool:
        if not isinstance(other, HDateTime):
            return False
        elif self.val != other.val:
            return False

        return True


@dataclass(frozen=True)
class HUri(HVal):
    val: str

    @staticmethod
    def make(val: str) -> HUri:
        return HUri(val)

    def __eq__(self, other: object, /) -> bool:
        return self.val == other.val if isinstance(other, HUri) else False


@dataclass(frozen=True)
class HStr(HVal):
    val: str

    @staticmethod
    def make(val: str) -> HStr:
        return HStr(val)

    def __eq__(self, other: object, /) -> bool:
        return self.val == other.val if isinstance(other, HStr) else False


@dataclass(frozen=True)
class HXstr(HVal):
    type_: Final[str]
    str_: Final[HStr]

    @staticmethod
    def make(type_: str, str_: HStr) -> HXstr:
        return HXstr(type_, str_)

    def __eq__(self, other: object, /) -> bool:
        if not isinstance(other, HXstr):
            return False
        elif self.type_ != other.type_:
            return False
        elif self.str_ != other.str_:
            return False

        return True


@dataclass(frozen=True)
class HList(HVal):
    @staticmethod
    def make(val: List[HVal]) -> HList:
        return HList(val)

    val: List[HVal]

    def __len__(self) -> int:
        return len(self.val)

    def __iter__(self) -> Iterator[HVal]:
        return iter(self.val)

    def __eq__(self, other: object, /) -> bool:
        if not isinstance(other, HList):
            return False
        elif len(self) != len(other):
            return False

        if any(map(lambda x: x[0] != x[1], zip(iter(self), iter(other)))):
            return False

        return True


@dataclass(frozen=True)
class HDict(HVal):
    val: Dict[str, HVal]

    @staticmethod
    def make(val: Dict[str, HVal]) -> HDict:
        return HDict(val)

    def __eq__(self, other: object, /) -> bool:
        if not isinstance(other, HDict):
            return False
        elif self.val != other.val:
            return False

        return True


@dataclass(frozen=True)
class HBin(HVal):
    mime: HStr

    @staticmethod
    def make(mime: HStr) -> HBin:
        return HBin(mime)

    def __eq__(self, other: object, /) -> bool:
        if not isinstance(other, HBin):
            return False
        elif self.mime != other.mime:
            return False

        return True


@dataclass(frozen=True)
class HBool(HVal):
    TRUE: ClassVar[HBool]
    FALSE: ClassVar[HBool]

    val: bool

    @staticmethod
    def make(val: bool) -> HBool:
        return HBool.TRUE if val else HBool.FALSE

    def __eq__(self, other: object, /) -> bool:
        return self.val == other.val if isinstance(other, HBool) else False


HBool.TRUE = HBool(True)
HBool.FALSE = HBool(False)


@dataclass(frozen=True)
class HNum(HVal):
    ZERO: ClassVar[HNum]
    POS_INF: ClassVar[HNum]
    NEG_INF: ClassVar[HNum]
    NaN: ClassVar[HNum]

    @staticmethod
    def make(val: float | int, unit: str | None = None) -> HNum:
        """
        Make a new number from the given value and (possible) unit.
        """

        val = float(val) if isinstance(val, int) else val

        # Use one of the already existing class instances if possible (
        #  leads to more efficient memory usage).
        if unit is None:
            if val == 0.0:
                return HNum.ZERO
            elif math.isnan(val):
                return HNum.NaN
            elif math.isinf(val):
                if val >= 0:
                    return HNum.POS_INF
                else:
                    return HNum.NEG_INF

        return HNum(val, unit)

    def __post_init__(self) -> None:
        """
        Make sure that the arguments passed are valid.
        """

        if self.unit is not None and not ZincGrammar.is_unit(self.unit):
            raise HVal.InvalidAttributeError(f"Invalid unit: '{self.unit}'")

    def __eq__(self, other: object, /) -> bool:
        if self is other:
            return True

        return self.val == other.val if isinstance(other, HNum) else False

    val: float
    unit: str | None = None


HNum.ZERO = HNum(0)
HNum.POS_INF = HNum(math.inf)
HNum.NEG_INF = HNum(-math.inf)
HNum.NaN = HNum(math.nan)


@dataclass(frozen=True)
class HCoord(HVal):
    @staticmethod
    def make(lat: float, lon: float) -> HCoord:
        return HCoord(lat, lon)

    lat: float
    lon: float

    def __post_init__(self) -> None:
        if not (-90.0 <= self.lat <= 90.0):
            raise HVal.InvalidAttributeError("Latitude out of range")
        elif not (-180.0 <= self.lon <= 180.0):
            raise HVal.InvalidAttributeError("Longitude out of range")


class HReader(ABC):
    @dataclass(frozen=True)
    class ReadException(Exception):
        message: str | None

    @abstractmethod
    def read_date(self, s: str) -> HDate:
        pass

    @abstractmethod
    def read_time(self, s: str) -> HTime:
        pass

    @abstractmethod
    def read_uri(self, s: str) -> HUri:
        pass

    @abstractmethod
    def read_str(self, s: str) -> HStr:
        pass

    @abstractmethod
    def read_bool(self, s: str) -> HBool:
        pass

    @abstractmethod
    def read_num(self, s: str) -> HNum:
        pass

    @abstractmethod
    def read_symbol(self, s: str) -> HSymbol:
        pass

    @abstractmethod
    def read_ref(self, s: str) -> HRef:
        pass

    @abstractmethod
    def read_date_time(self, s: str) -> HDateTime:
        pass


class HZincReader(HReader):
    _enc_date_len: ClassVar[int] = len("YYYY-MM-DD")
    _enc_plain_time_len: ClassVar[int] = len("HH-MM-SS")

    def read_date(self, s: str) -> HDate:
        return HDate.make(date.fromisoformat(s))

    def read_time(self, s: str) -> HTime:
        return HTime.make(time.fromisoformat(s))

    def read_uri(self, s: str) -> HUri:
        """
        Read a single URI from the zinc format.
        """

        if len(s) < 2:
            raise HReader.ReadException("Valid URI cannot be less than two chars.")

        if s[0] != "`":
            raise HReader.ReadException("Missing '`' at start of URI")

        r: List[str] = []

        end: bool = False

        i: int = 1
        while i < len(s):
            cur: str = s[i]
            peek: str | None = s[i + 1] if i + 1 < len(s) else None

            if cur == "`":
                end = True
                i += 1
                break
            elif cur == "\\":
                if peek in [":", "/", "?", "#", "[", "]", "@", "\\", "&", "=", ";"]:
                    r.append(cur)
                elif peek in ["`"]:
                    pass
                else:
                    raise HReader.ReadException(f"Invalid escaped char: '{peek}'")

                r.append(peek)
                i += 1
            else:
                r.append(cur)

            i += 1

        if not end:
            raise HReader.ReadException("URI not terminated properly.")

        if i != len(s):
            raise HReader.ReadException(f"Jibberish after URI: '{s[i:]}'")

        return HUri.make("".join(r))

    def read_str(self, s: str) -> HStr:
        """
        Read a single URI from the zinc format.
        """

        if len(s) < 2:
            raise HReader.ReadException("Valid STR cannot be less than two chars.")

        if s[0] != '"':
            raise HReader.ReadException("Missing '\"' at start of STR")

        r: List[str] = []

        end: bool = False

        i: int = 1
        while i < len(s):
            cur: str = s[i]
            peek: str | None = s[i + 1] if i + 1 < len(s) else None

            if cur == '"':
                end = True
                break
            elif cur == "\\":
                match peek:
                    case "b":
                        r.append("\b")
                    case "f":
                        r.append("\f")
                    case "n":
                        r.append("\n")
                    case "r":
                        r.append("\r")
                    case "t":
                        r.append("\t")
                    case "\\":
                        r.append("\\")
                    case "$":
                        r.append("$")
                    case '"':
                        r.append('"')
                    case "u":
                        if i + 4 >= len(s):
                            raise HReader.ReadException("Unicode sequence too short.")

                        seq: str = s[i + 2 : i + 6]
                        r.append(chr(int(seq, 16)))

                        i += 4
                    case _:
                        raise HReader.ReadException(f"Invalid escaped char: '{peek}'")

                i += 1
            else:
                r.append(cur)

            i += 1

        if not end:
            raise HReader.ReadException("STR not terminated properly.")

        return HStr.make("".join(r))

    def read_bool(self, s: str) -> HBool:
        """
        Read a boolean from the given string.
        """

        match s:
            case "T":
                return HBool.TRUE
            case "F":
                return HBool.FALSE
            case _:
                raise HReader.ReadException(
                    f"Invalid boolean expected 'T' or 'F', got: '{s}'"
                )

    def read_num(self, s: str) -> HNum:
        """
        Read a number from the given string.
        """

        # Read the string as NaN, INF or -INF if needed.
        if ZincGrammar.is_nan(s):
            return HNum.NaN
        elif ZincGrammar.is_pos_inf(s):
            return HNum.POS_INF
        elif ZincGrammar.is_neg_inf(s):
            return HNum.NEG_INF

        i = 0

        sign: int = 1

        if s[i] == "-":
            sign = -1
            i += 1

        j = i

        if not ZincGrammar.is_digits_start(s[i]):
            raise HReader.ReadException("Expected digits")

        i += 1

        while i < len(s):
            if not ZincGrammar.is_digits_part(s[i]):
                break
            i += 1

        digits: str = s[j:i]
        decimals: str | None = None
        exponent_sign: int = 1
        exponent: str | None = None
        unit: str | None = None

        # Handle the case we're dealing with decimals.
        if i < len(s) and s[i] == ".":
            i += 1

            j = i

            if i == len(s) or not ZincGrammar.is_digits_start(s[i]):
                raise HReader.ReadException("Expected decimals after the comma")

            i += 1

            while i < len(s):
                if not ZincGrammar.is_digits_part(s[i]):
                    break
                i += 1

            decimals = s[j:i]

        # Handle the case we're dealing with an exponent.
        if (
            i + 1 < len(s)
            and s[i] in ["e", "E"]
            and (s[i + 1] in ["-", "+"] or ZincGrammar.is_digit(s[i + 1]))
        ):
            i += 1

            # Check if we're dealing with a positive or negative exponent.
            if i < len(s) and s[i] == "+":
                i += 1
            elif i < len(s) and s[i] == "-":
                exponent_sign = -1
                i += 1

            j = i

            # Read the digits of the exponent.
            if i == len(s) or not ZincGrammar.is_digits_start(s[i]):
                raise HReader.ReadException("Invalid exponent, expected decimals.")

            i += 1

            while i < len(s):
                if not ZincGrammar.is_digits_part(s[i]):
                    break
                i += 1

            exponent = s[j:i]

        # Read the unit.
        j = i
        while i < len(s):
            if not ZincGrammar.is_unit_char(s[i]):
                break
            i += 1

        # Get the unit if it was read.
        if j != i:
            unit = s[j:i]

        # Check if there is anything left in the string, if that's
        #  the case then raise an error because there is jibberish.
        if i != len(s):
            raise HReader.ReadException(f"Jibberish after number: '{s[i:]}'")

        num: float = sign * float(digits)

        if decimals:
            num += sign * (float(decimals) / (10.0 ** len(decimals)))

        if exponent:
            num *= 10 ** (exponent_sign * float(exponent))

        return HNum(num, unit)

    def read_symbol(self, s: str) -> HSymbol:
        if len(s) < 2:
            raise HReader.ReadException(
                "Symbol length should be at least two characters."
            )

        if not ZincGrammar.is_symbol_start(s[0]):
            raise HReader.ReadException(f"Symbol start is not valid.")

        for i in range(1, len(s)):
            if not ZincGrammar.is_symbol_part(s[i]):
                raise HReader.ReadException("Invalid symbol")

        return HSymbol.make(s[1:])

    def read_ref(self, s: str) -> HRef:
        """
        Read a ref from the given zinc string.
        :param s: The zinc string.
        :return: The read ref.
        """

        # We do not read the string that can possibly be found after a ref,
        #  due to the pure-laziness of both me and the original designers of
        #  the zinc format, this will be handled in the second phase of parsing.

        if len(s) < 2:
            raise HReader.ReadException("Ref length should be at least two characters.")

        if not ZincGrammar.is_ref_start(s[0]):
            raise HReader.ReadException(f"Ref start is not valid.")

        for i in range(1, len(s)):
            if ZincGrammar.is_ref_end(s[i]):
                i += 1
                
                if i < len(s):
                    raise HReader.ReadException(f"Ref is not valid.")

                break

            if not ZincGrammar.is_ref_part(s[i]):
                raise HReader.ReadException(f"Invalid ref: {s}")

        return HRef.make(s[1:])

    def read_date_time(self, s: str) -> HDateTime:
        idx: int = s.find(" ")

        if idx != -1:
            s = s[: idx]

        return HDateTime.make(datetime.fromisoformat(s))
