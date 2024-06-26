from __future__ import annotations
from dataclasses import dataclass
from typing import ClassVar, List
from abc import ABC, abstractmethod


class HVal(ABC):
    @dataclass(frozen=True)
    class InvalidAttributeError(Exception):
        message: str | None

    @abstractmethod
    def read(self, reader: HReader, s: str) -> HVal:
        pass

    @abstractmethod
    def __str__(self) -> str:
        pass


@dataclass(frozen=True)
class HDate(HVal):
    year: int
    month: int
    day: int

    @staticmethod
    def make(year: int, month: int, day: int) -> HDate:
        if year < 1900:
            raise HDate.InvalidAttributeError(f"Invalid year: '{year}'")
        elif month < 1 or month > 12:
            raise HDate.InvalidAttributeError(f"Invalid month: '{month}'")
        elif day < 1 or day > 31:
            raise HDate.InvalidAttributeError(f"Invalid day: '{day}'")

        return HDate(year, month, day)

    def read(self, reader: HReader, s: str) -> HVal:
        return reader.read_date(s)

    def __str__(self) -> str:
        return f"{str(self.year).zfill(4)}:{str(self.month).zfill(2)}:{str(self.day).zfill(2)}"


@dataclass(frozen=True)
class HTime(HVal):
    hour: int
    min: int
    sec: int
    ms: int

    @staticmethod
    def make(hour: int, min: int, sec: int, ms: int = 0) -> HTime:
        if hour < 0 or hour > 23:
            raise HVal.InvalidAttributeError(f"Invalid hours: '{hour}'")
        elif min < 0 or min > 59:
            raise HVal.InvalidAttributeError(f"Invalid minutes: '{min}'")
        elif sec < 0 or sec > 23:
            raise HVal.InvalidAttributeError(f"Invalid seconds: '{sec}'")
        elif ms < 0 or ms > 999:
            raise HVal.InvalidAttributeError(f"Invalid milliseconds: '{ms}'")

        return HTime(hour, min, sec, ms)

    def read(self, reader: HReader, s: str) -> HVal:
        return reader.read_time(s)

    def __str__(self) -> str:
        return f"{str(self.hour).zfill(2)}:{str(self.min).zfill(2)}:{str(self.sec).zfill(2)}.{str(self.ms).zfill(3)}"


@dataclass(frozen=True)
class HUri(HVal):
    val: str

    @staticmethod
    def make(val: str) -> HUri:
        return HUri(val)

    def read(self, reader: HReader, s: str) -> HVal:
        return reader.read_uri(s)

    def __str__(self) -> str:
        return self.val


@dataclass(frozen=True)
class HStr(HVal):
    val: str

    @staticmethod
    def make(val: str) -> HStr:
        return HStr(val)

    def read(self, reader: HReader, s: str) -> HVal:
        return reader.read_str(s)

    def __str__(self) -> str:
        return self.val


@dataclass(frozen=True)
class HBool(HVal):
    TRUE: ClassVar[HBool]
    FALSE: ClassVar[HBool]

    val: bool

    @staticmethod
    def make(val: bool) -> HBool:
        return HBool.TRUE if val else HBool.FALSE

    def read(self, reader: HReader, s: str) -> HVal:
        return reader.read_bool(s)

    def __str__(self) -> str:
        return str(self.val)


HBool.TRUE = HBool(True)
HBool.FALSE = HBool(False)


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


class HZincReader(HReader):
    _enc_date_len: ClassVar[int] = len("YYYY-MM-DD")
    _enc_plain_time_len: ClassVar[int] = len("HH-MM-SS")

    def read_date(self, s: str) -> HDate:
        """
        Read a date from the given zinc-formatted string.
        """

        if len(s) < HZincReader._enc_date_len:
            raise HReader.ReadException(
                f"Invalid date size, expected {HZincReader._enc_date_len}, got {len(s)}"
            )

        try:
            year: int = int(s[0:4])
        except ValueError:
            raise HReader.ReadException(f"Invalid year: '{s[0:4]}'")

        if s[4] != "-":
            raise HReader.ReadException(f"Date '{s}' is not properly formatted.")

        try:
            month: int = int(s[5:7])
        except ValueError:
            raise HReader.ReadException(f"Invalid month: '{s:5:7}'")

        if s[7] != "-":
            raise HReader.ReadException(f"Date '{s}' is not properly formatted.")

        try:
            day: int = int(s[8:10])
        except ValueError:
            raise HReader.ReadException(f"Invalid day: '{s[8:10]}'")

        return HDate.make(year, month, day)

    def read_time(self, s: str) -> HTime:
        """
        Read a time from the given zinc-formatted string.
        """

        if len(s) < HZincReader._enc_plain_time_len:
            raise HReader.ReadException(
                f"Invalid time len, expected {HZincReader._enc_plain_time_len}, got: {len(s)}"
            )

        try:
            hour: int = int(s[0:2])
        except ValueError:
            raise HReader.ReadException(f"Invalid hour: '{s[0:2]}'")

        if s[2] != ":":
            raise HReader.ReadException(
                f"Time '{s}' is not properly formatted (missing first colon)."
            )

        try:
            min: int = int(s[3:5])
        except ValueError:
            raise HReader.ReadException(f"Invalid minute: '{s[3:5]}'")

        if s[5] != ":":
            raise HReader.ReadException(
                f"Time '{s}' is not properly formatted (missing second colon)."
            )

        try:
            sec: int = int(s[6:8])
        except ValueError:
            raise HReader.ReadException(f"Invalid second: '{s[6:8]}'")

        if len(s) == HZincReader._enc_plain_time_len:
            return HTime.make(hour, min, sec)

        if s[8] != ".":
            raise HReader.ReadException(
                f"Time '{s}' is not properly formatted (missing dot)."
            )

        ms: int = 0
        pos: int = 9
        places: int = 0
        len_: int = len(s)

        while pos < len_ and places < 3:
            ms = (ms * 10) + int(s[pos])
            pos += 1
            places += 1

        if places == 1:
            ms *= 100
        elif places == 2:
            ms *= 10
        elif places == 3:
            pass
        else:
            raise HReader.ReadException(f"Time '{s}' has too many fractional digits.")

        return HTime.make(hour, min, sec, ms)

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
        Read a boolean fro the given string.
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
