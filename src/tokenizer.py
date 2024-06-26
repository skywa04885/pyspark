from enum import Enum
from dataclasses import dataclass
from ztypes import HDate, HZincReader, HVal


class Characters:
    @staticmethod
    def is_unit_char(c: str) -> bool:
        return (
            Characters.is_alpha(c)
            or c == "%"
            or c == "_"
            or c == "/"
            or c == "$"
            or ord(c) > 128
        )

    @staticmethod
    def is_alpha_lo(c: str) -> bool:
        return ord("a") <= ord(c) <= ord("z")

    @staticmethod
    def is_alpha_hi(c: str) -> bool:
        return ord("A") <= ord(c) <= ord("Z")

    @staticmethod
    def is_alpha(c: str) -> bool:
        return Characters.is_alpha_lo(c) or Characters.is_alpha_hi(c)

    @staticmethod
    def is_digit(c: str) -> bool:
        return ord("0") <= ord(c) <= ord("9")

    @staticmethod
    def is_hex_digit(c: str) -> bool:
        return (
            ord("a") <= ord(c) <= ord("f")
            or ord("A") <= ord(c) <= ord("F")
            or Characters.is_digit(c)
        )

    @staticmethod
    def is_ref_char(c: str) -> bool:
        return (
            Characters.is_alpha(c)
            or Characters.is_digit(c)
            or c == "_"
            or c == ":"
            or c == "-"
            or c == "."
            or c == "~"
        )

    @staticmethod
    def is_id_start(c: str) -> bool:
        return Characters.is_alpha_lo(c)

    @staticmethod
    def is_id_part(c: str) -> bool:
        return Characters.is_alpha(c) or Characters.is_digit(c) or c == "_"

    @staticmethod
    def is_keyword_start(c: str) -> bool:
        return Characters.is_alpha_hi(c)

    @staticmethod
    def is_keyword_part(c: str) -> bool:
        return Characters.is_alpha(c)

    @staticmethod
    def is_ref_start(c: str) -> bool:
        return c == "@"

    @staticmethod
    def is_ref_part(c: str) -> bool:
        return Characters.is_ref_char(c)

    @staticmethod
    def is_ref_end(c: str) -> bool:
        return c == " "

    @staticmethod
    def is_symbol_start(c: str) -> bool:
        return c == "^"

    @staticmethod
    def is_symbol_part(c: str) -> bool:
        return Characters.is_ref_char(c)

    @staticmethod
    def is_str_start(c: str) -> bool:
        return c == '"'

    @staticmethod
    def is_str_regular_escaped_char(c: str) -> bool:
        return c in ["b", "f", "n", "r", "t", "\\", "$", '"']

    @staticmethod
    def is_str_end(c: str) -> bool:
        return c == '"'

    @staticmethod
    def is_uri_start(c: str) -> bool:
        return c == "`"

    @staticmethod
    def is_uri_regular_escaped_char(c: str) -> bool:
        return c in [
            ":",
            "/",
            "?",
            "#",
            "[",
            "]",
            "@",
            "`",
            "\\",
            "&",
            "=",
            ";",
        ]

    @staticmethod
    def is_uri_end(c: str) -> bool:
        return c == "`"

    @staticmethod
    def is_whitespace(c: str) -> bool:
        return c == " " or c == "\t" or ord(c) == 0xA0

    @staticmethod
    def is_unicode_char(c: str) -> bool:
        return ord(c) >= 0x20


class TokenType(Enum):
    KEYWORD = 0
    IDENTIFIER = 1
    WHITESPACE = 2
    SYMBOL = 3
    REF = 4
    STR = 5
    DATE = 6
    DATETIME = 7
    TIME = 8
    URI = 9
    NUMBER = 10
    BOOL = 11


@dataclass(frozen=True)
class Token:
    t: TokenType
    s: str
    beg: int
    end: int
    val: HVal | None = None

    def __len__(self) -> int:
        return self.end - self.beg

    def __str__(self) -> str:
        return self.s[self.beg : self.end]

    def __repr__(self) -> str:
        return f"{self.t} ({str(self)}) {str(self.val)}"


@dataclass(frozen=True)
class Tokenizer:
    @dataclass(frozen=True)
    class ParseException(Exception):
        message: str

    class StrReader:
        _str: str
        _begin: int  # The beginning of the being read token.
        _head: int

        def __init__(self, str_: str) -> None:
            self._str = str_
            self._begin = 0
            self._head = 0

        def consume(self, expect: str | None = None) -> None:
            if expect is not None and self.cur != expect:
                raise Tokenizer.ParseException(
                    f"Expected '{expect}' got '{self.cur}' instead"
                )

            self.next()

        def next(self) -> None:
            self._head += 1

        @property
        def token_slice(self) -> str:
            return self._str[self._begin : self._head]

        @property
        def token_len(self) -> int:
            return self._head - self._begin

        def extract_token(self, t: TokenType, val: HVal | None = None) -> Token:
            token: Token = Token(t, self._str, self._begin, self._head, val)
            self._begin = self._head
            return token

        @property
        def peek(self) -> str | None:
            peek_index: int = self._head + 1

            if peek_index >= len(self._str):
                return None

            return self._str[peek_index]

        @property
        def cur(self) -> str | None:
            return self._str[self._head] if self._head < len(self._str) else None

    reader: StrReader
    zinc_reader: HZincReader = HZincReader()

    def next_whitespace(self) -> Token:
        """
        Read whitespace from the reader.
        """

        while self.reader.cur is not None and Characters.is_whitespace(self.reader.cur):
            self.reader.consume()

        return self.reader.extract_token(TokenType.WHITESPACE)

    def next_identifier(self) -> Token:
        """
        Read an identifier from the reader.
        """

        assert self.reader.cur is not None

        # Make sure that the first character we're reading actually is the start of an id.
        if not Characters.is_id_start(self.reader.cur):
            raise Tokenizer.ParseException(f"Invalid id start '{self.reader.cur}'")

        # Consume the start character.
        self.reader.consume()

        # Consume all the characters that belong to the id.
        while self.reader.cur is not None and Characters.is_id_part(self.reader.cur):
            self.reader.consume()

        # Extract the token from the read part.
        return self.reader.extract_token(TokenType.IDENTIFIER)

    def next_keyword(self) -> Token:
        """
        Read a keyword from the reader.
        """

        assert self.reader.cur is not None

        # Make sure that the first character we're reading actually is the start of an keyword.
        if not Characters.is_keyword_start(self.reader.cur):
            raise Tokenizer.ParseException(f"Invalid keyword start '{self.reader.cur}'")

        # Consume the start character.
        self.reader.consume()

        # Consume all the characters that belong to the keyword.
        while self.reader.cur is not None and Characters.is_keyword_part(
            self.reader.cur
        ):
            self.reader.consume()

        # We might deal with "INF" or "NaN" which will be numbers. This is an edge-case
        #  we need to keep in mind, thanks to the wonderful design of this format.
        if self.reader.token_slice in ["INF", "NaN"]:
            return self.reader.extract_token(TokenType.NUMBER)

        # We might deal with "T" or "F" which will be booleans.
        if self.reader.token_slice in ["T", "F"]:
            return self.reader.extract_token(
                TokenType.BOOL, self.zinc_reader.read_bool(self.reader.token_slice)
            )

        # Extract the token from the read part.
        return self.reader.extract_token(TokenType.KEYWORD)

    def next_symbol(self) -> Token:
        """
        Read a symbol from the reader.
        """

        assert self.reader.cur

        # Make sure that the first character we're reading actually is the start of a symbol.
        if not Characters.is_symbol_start(self.reader.cur):
            raise Tokenizer.ParseException(f"Invalid symbol start '{self.reader.cur}'")

        # Consume the start character.
        self.reader.consume()

        # Consume all the characters that belong to the symbol.
        while self.reader.cur is not None and Characters.is_symbol_part(
            self.reader.cur
        ):
            self.reader.consume()

        # Extract the token from the read part.
        return self.reader.extract_token(TokenType.SYMBOL)

    def next_ref(self) -> Token:
        """
        Read a ref from the reader.
        """

        assert self.reader.cur

        # Make sure that the first character we're reading actually is the start of a ref.
        if not Characters.is_ref_start(self.reader.cur):
            raise Tokenizer.ParseException(f"Invalid ref start '{self.reader.cur}'")

        # Consume the start character.
        self.reader.consume()

        # Consume all the characters that belong to the ref.
        while self.reader.cur is not None and Characters.is_ref_part(self.reader.cur):
            self.reader.consume()

        # Consume the trailing whitespace if it is there.
        if self.reader.cur is not None and Characters.is_ref_end(self.reader.cur):
            self.reader.consume()

        # Extract the token from the read part.
        return self.reader.extract_token(TokenType.REF)

    def next_str(self) -> Token:
        """
        Read a single str from the reader.
        """

        assert self.reader.cur

        # Make sure that the first character we're reading actually is the start of a string.
        if not Characters.is_str_start(self.reader.cur):
            raise Tokenizer.ParseException(f"Invalid str start '{self.reader.cur}'")

        # Consume the start character.
        self.reader.consume()

        end: bool = False

        while True:
            # Break if we've reached the end of the reader.
            if self.reader.cur is None:
                break

            # Handle the case we've gotten an escaped character.
            if self.reader.cur == "\\":
                self.reader.consume()

                # Make sure that there is another char.
                if self.reader.cur is None:
                    raise Tokenizer.ParseException("Unexpected EOF after string ESCAPE")

                # Handle the case we're dealing with a regular escaped character.
                if Characters.is_str_regular_escaped_char(self.reader.cur):
                    self.reader.consume()
                # Handle the case we're dealing with an unicode character.
                elif self.reader.cur == "u":
                    self.reader.consume()

                    for _ in range(0, 4):
                        # Make sure there was more to read.
                        if self.reader.cur is None:
                            raise Tokenizer.ParseException(
                                "Incomplete unicode escape char"
                            )

                        # Make sure we've read a hex digit.
                        if not Characters.is_hex_digit(self.reader.cur):
                            raise Tokenizer.ParseException(
                                f"Invalid hex digit: '{self.reader.cur}'"
                            )

                        # Consume the read hex digit.
                        self.reader.consume()
                else:
                    raise Tokenizer.ParseException(
                        f"Unexpected escaped character {self.reader.cur}"
                    )
            # Handle the case we got the end of a string.
            elif Characters.is_str_end(self.reader.cur):
                self.reader.consume()
                end = True
                break
            # Handle the case we've gotten an regular unicode character.
            elif Characters.is_unicode_char(self.reader.cur):
                self.reader.consume()
            # Handle the case the character cannot be recognized.
            else:
                raise Tokenizer.ParseException(
                    f"Invalid character in string: '{self.reader.cur}'"
                )

        # Make sure the string was ended.
        if not end:
            raise Tokenizer.ParseException("STR not terminated")

        # Extract the token from the read part.
        return self.reader.extract_token(
            TokenType.STR, self.zinc_reader.read_str(self.reader.token_slice)
        )

    def next_uri(self) -> Token:
        """
        Read a single uri from the reader.
        """

        assert self.reader.cur

        # Make sure that the first character we're reading actually is the start of a uri.
        if not Characters.is_uri_start(self.reader.cur):
            raise Tokenizer.ParseException(f"Invalid URI start '{self.reader.cur}'")

        # Consume the start character.
        self.reader.consume()

        end: bool = False

        while True:
            # Break if we've reached the end of the reader.
            if self.reader.cur is None:
                break

            # Handle the case we've gotten an escaped character.
            if self.reader.cur == "\\":
                self.reader.consume()

                # Make sure that there is another char.
                if self.reader.cur is None:
                    raise Tokenizer.ParseException("Unexpected EOF after URI ESCAPE")

                # Handle the case we're dealing with a regular escaped character.
                if Characters.is_uri_regular_escaped_char(self.reader.cur):
                    self.reader.consume()
                # Handle the case we're dealing with an unicode character.
                elif self.reader.cur == "u":
                    self.reader.consume()

                    for _ in range(0, 4):
                        # Make sure there was more to read.
                        if self.reader.cur is None:
                            raise Tokenizer.ParseException(
                                "Incomplete unicode escape char in URI"
                            )

                        # Make sure we've read a hex digit.
                        if not Characters.is_hex_digit(self.reader.cur):
                            raise Tokenizer.ParseException(
                                f"Invalid hex digit: '{self.reader.cur}'"
                            )

                        # Consume the read hex digit.
                        self.reader.consume()
                else:
                    raise Tokenizer.ParseException(
                        f"Unexpected escaped character inside URI {self.reader.cur}"
                    )

            # Handle the case we got the end of a URI.
            elif Characters.is_uri_end(self.reader.cur):
                self.reader.consume()
                end = True
                break
            # Handle the case we've gotten an regular unicode character.
            elif Characters.is_unicode_char(self.reader.cur):
                self.reader.consume()
            # Handle the case the character cannot be recognized.
            else:
                raise Tokenizer.ParseException(
                    f"Invalid character in URI: '{self.reader.cur}'"
                )

        # Make sure the string was ended.
        if not end:
            raise Tokenizer.ParseException("URI not terminated")

        # Extract the token from the read part.
        return self.reader.extract_token(
            TokenType.URI, self.zinc_reader.read_uri(self.reader.token_slice)
        )

    def next_num(self) -> Token:
        """
        Reads the next number, date, time or date time.
        """

        assert self.reader.cur is not None

        # Handle the case we're dealing with a hex number.
        if self.reader.cur == "0" and self.reader.peek == "x":
            # Consume the start of the hex number.
            self.reader.consume("0")
            self.reader.consume("x")

            # Keep consuming the hex digits.
            while self.reader.cur is not None and (
                Characters.is_hex_digit(self.reader.cur) or self.reader.cur == "_"
            ):
                self.reader.consume()

            # Make sure the hex number actually has contents.
            if self.reader.token_len == 2:
                raise Tokenizer.ParseException("Incomplete hex number")

            # Return the token.
            return self.reader.extract_token(TokenType.NUMBER)

        colons: int = 0
        dashes: int = 0
        unit_found: bool = False
        exp: bool = False

        while self.reader.cur is not None:
            if Characters.is_digit(self.reader.cur):
                self.reader.consume()
            elif exp and self.reader.cur in ["+", "-"]:
                pass
            elif self.reader.cur == "-":
                dashes += 1
            elif (
                self.reader.cur == ":"
                and self.reader.peek is not None
                and Characters.is_digit(self.reader.peek)
            ):
                colons += 1
            elif (exp or colons >= 1) and self.reader.cur == "+":
                pass
            elif self.reader.cur == ".":
                if self.reader.peek is None or not Characters.is_digit(
                    self.reader.peek
                ):
                    break
            elif (
                self.reader.cur in ["e", "E"]
                and self.reader.peek is not None
                and (
                    self.reader.peek in ["-", "+"]
                    or Characters.is_digit(self.reader.peek)
                )
            ):
                exp = True
            elif (
                Characters.is_alpha(self.reader.cur)
                or self.reader.cur in ["%", "$", "/"]
                or ord(self.reader.cur) > 128
            ):
                unit_found = True
            elif self.reader.cur == "_":
                if unit_found and Characters.is_digit(self.reader.cur):
                    self.reader.consume()
                    continue
                else:
                    unit_found = True
            else:
                break

            self.reader.consume()

        # If there are two dashes and zero colons, we might deal with a date.
        if dashes == 2 and colons == 0:
            return self.reader.extract_token(
                TokenType.DATE, self.zinc_reader.read_date(self.reader.token_slice)
            )

        # If there are zero dashes, and more than one colon, we might deal with time.
        if dashes == 0 and colons > 1:
            return self.reader.extract_token(
                TokenType.TIME, self.zinc_reader.read_time(self.reader.token_slice)
            )

        # If there are more than two dashes, we might deal with datetime.

        return self.reader.extract_token(TokenType.NUMBER)

    def next(self) -> Token | None:
        """
        Read the next token or return None if not existing.
        """

        # If there can not be read any more tokens, simply return None.
        if self.reader.cur is None:
            return None

        if Characters.is_whitespace(self.reader.cur):
            return self.next_whitespace()
        elif Characters.is_id_start(self.reader.cur):
            return self.next_identifier()
        elif Characters.is_keyword_start(self.reader.cur):
            return self.next_keyword()
        elif Characters.is_symbol_start(self.reader.cur):
            return self.next_symbol()
        elif Characters.is_ref_start(self.reader.cur):
            return self.next_ref()
        elif Characters.is_str_start(self.reader.cur):
            return self.next_str()
        elif Characters.is_uri_start(self.reader.cur):
            return self.next_uri()
        elif Characters.is_digit(self.reader.cur) or self.reader.cur == "-":
            return self.next_num()
        else:
            raise Tokenizer.ParseException(f"Unexpected char '{self.reader.cur}'")


a = Tokenizer(
    Tokenizer.StrReader(
        'aSUAUDIHIU AA    ^asd aA @:asd "asd \\" hello \\u2713" `http://hello world\\`` NaN INF 0x00 2004-02-12 23:04:01 T F '
    )
)
while True:
    tok = a.next()
    if tok is None:
        break
    print(repr(tok))
