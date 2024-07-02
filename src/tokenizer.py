from enum import Enum
from dataclasses import dataclass
from ztypes import HZincReader
from typing import AsyncGenerator, Dict, Final

from zinc.grammer import ZincGrammar
from zinc.token import ZincTokenType, ZincToken


TRIVIAL_TOKEN_TABLE: Final[Dict[str, ZincTokenType]] = {
    "(": ZincTokenType.LPAREN,
    ")": ZincTokenType.RPAREN,
    "[": ZincTokenType.LBRACKET,
    "]": ZincTokenType.RBRACKET,
    "{": ZincTokenType.LBRACE,
    "}": ZincTokenType.RBRACE,
    ":": ZincTokenType.COLON,
    ",": ZincTokenType.COMMA,
    "\n": ZincTokenType.LINEFEED,
}


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

        def consume(self, expect: str | None = None, reset: bool = False) -> None:
            if expect is not None and self.cur != expect:
                raise Tokenizer.ParseException(
                    f"Expected '{expect}' got '{self.cur}' instead"
                )

            self.next()

            if reset:
                self._begin = self._head

        def next(self) -> None:
            self._head += 1

        @property
        def token_slice(self) -> str:
            return self._str[self._begin : self._head]

        @property
        def token_len(self) -> int:
            return self._head - self._begin

        def extract_token(self, t: ZincTokenType) -> ZincToken:
            token: ZincToken = ZincToken(t, self._str[self._begin:self._head])
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

    def next_identifier(self) -> ZincToken:
        """
        Read an identifier from the reader.
        """

        assert self.reader.cur is not None

        # Make sure that the first character we're reading actually is the start of an id.
        if not ZincGrammar.is_id_start(self.reader.cur):
            raise Tokenizer.ParseException(f"Invalid id start '{self.reader.cur}'")

        # Consume the start character.
        self.reader.consume()

        # Consume all the characters that belong to the id.
        while self.reader.cur is not None and ZincGrammar.is_id_part(self.reader.cur):
            self.reader.consume()

        # Extract the token from the read part.
        return self.reader.extract_token(ZincTokenType.IDENTIFIER)

    def next_keyword(self) -> ZincToken:
        """
        Read a keyword from the reader.
        """

        assert self.reader.cur is not None

        # Make sure that the first character we're reading actually is the start of an keyword.
        if not ZincGrammar.is_keyword_start(self.reader.cur):
            raise Tokenizer.ParseException(f"Invalid keyword start '{self.reader.cur}'")

        # Consume the start character.
        self.reader.consume()

        # Consume all the characters that belong to the keyword.
        while self.reader.cur is not None and ZincGrammar.is_keyword_part(
            self.reader.cur
        ):
            self.reader.consume()

        match self.reader.token_slice:
            case "NaN" | "INF":
                return self.reader.extract_token(ZincTokenType.NUMBER)
            case "T" | "F":
                return self.reader.extract_token(ZincTokenType.BOOL)

        # Extract the token from the read part.
        return self.reader.extract_token(ZincTokenType.KEYWORD)

    def next_symbol(self) -> ZincToken:
        """
        Read a symbol from the reader.
        """

        assert self.reader.cur

        # Make sure that the first character we're reading actually is the start of a symbol.
        if not ZincGrammar.is_symbol_start(self.reader.cur):
            raise Tokenizer.ParseException(f"Invalid symbol start '{self.reader.cur}'")

        # Consume the start character.
        self.reader.consume()

        # Consume all the characters that belong to the symbol.
        while self.reader.cur is not None and ZincGrammar.is_symbol_part(
            self.reader.cur
        ):
            self.reader.consume()

        # Extract the token from the read part.
        return self.reader.extract_token(ZincTokenType.SYMBOL)

    def next_ref(self) -> ZincToken:
        """
        Read a ref from the reader.
        """

        assert self.reader.cur

        # Make sure that the first character we're reading actually is the start of a ref.
        if not ZincGrammar.is_ref_start(self.reader.cur):
            raise Tokenizer.ParseException(f"Invalid ref start '{self.reader.cur}'")

        # Consume the start character.
        self.reader.consume()

        # Consume all the characters that belong to the ref.
        while self.reader.cur is not None and ZincGrammar.is_ref_part(self.reader.cur):
            self.reader.consume()

        # Extract the token from the read part.
        return self.reader.extract_token(ZincTokenType.REF)

    def next_str(self) -> ZincToken:
        """
        Read a single str from the reader.
        """

        assert self.reader.cur

        # Make sure that the first character we're reading actually is the start of a string.
        if not ZincGrammar.is_str_start(self.reader.cur):
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
                if ZincGrammar.is_str_escaped_char(self.reader.cur):
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
                        if not ZincGrammar.is_hex_digit(self.reader.cur):
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
            elif ZincGrammar.is_str_end(self.reader.cur):
                self.reader.consume()
                end = True
                break
            # Handle the case we've gotten an regular unicode character.
            elif ZincGrammar.is_unicode_char(self.reader.cur):
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
        return self.reader.extract_token(ZincTokenType.STR)

    def next_uri(self) -> ZincToken:
        """
        Read a single uri from the reader.
        """

        assert self.reader.cur

        # Make sure that the first character we're reading actually is the start of a uri.
        if not ZincGrammar.is_uri_start(self.reader.cur):
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
                if ZincGrammar.is_uri_escaped_char(self.reader.cur):
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
                        if not ZincGrammar.is_hex_digit(self.reader.cur):
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
            elif ZincGrammar.is_uri_end(self.reader.cur):
                self.reader.consume()
                end = True
                break
            # Handle the case we've gotten an regular unicode character.
            elif ZincGrammar.is_unicode_char(self.reader.cur):
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
        return self.reader.extract_token(ZincTokenType.URI)

    def next_num(self) -> ZincToken:
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
                ZincGrammar.is_hex_digit(self.reader.cur) or self.reader.cur == "_"
            ):
                self.reader.consume()

            # Make sure the hex number actually has contents.
            if self.reader.token_len == 2:
                raise Tokenizer.ParseException("Incomplete hex number")

            # Return the token.
            return self.reader.extract_token(ZincTokenType.NUMBER)

        colons: int = 0
        dashes: int = 0
        unit_found: bool = False
        exp: bool = False

        while self.reader.cur is not None:
            if ZincGrammar.is_digit(self.reader.cur):
                self.reader.consume()
                continue
            elif exp and self.reader.cur in ["+", "-"]:
                pass
            elif self.reader.cur == "-":
                dashes += 1
            elif (
                self.reader.cur == ":"
                and self.reader.peek is not None
                and ZincGrammar.is_digit(self.reader.peek)
            ):
                colons += 1
            elif (exp or colons >= 1) and self.reader.cur == "+":
                pass
            elif self.reader.cur == ".":
                if self.reader.peek is None or not ZincGrammar.is_digit(
                    self.reader.peek
                ):
                    break
            elif (
                self.reader.cur in ["e", "E"]
                and self.reader.peek is not None
                and (
                    self.reader.peek in ["-", "+"]
                    or ZincGrammar.is_digit(self.reader.peek)
                )
            ):
                exp = True
            elif (
                ZincGrammar.is_alpha(self.reader.cur)
                or self.reader.cur in ["%", "$", "/"]
                or ord(self.reader.cur) > 128
            ):
                unit_found = True
            elif self.reader.cur == "_":
                if unit_found and ZincGrammar.is_digit(self.reader.cur):
                    self.reader.consume()
                    continue
                else:
                    unit_found = True
            else:
                break

            self.reader.consume()

        # If there are two dashes and zero colons, we might deal with a date.
        if dashes == 2 and colons == 0:
            return self.reader.extract_token(ZincTokenType.DATE)

        # If there are zero dashes, and more than one colon, we might deal with time.
        if dashes == 0 and colons > 1:
            return self.reader.extract_token(ZincTokenType.TIME)

        # If there are more than two dashes, we might deal with datetime.

        return self.reader.extract_token(ZincTokenType.NUMBER)

    def next(self) -> ZincToken | None:
        """
        Read the next token or return None if not existing.
        """

        while self.reader.cur is not None and ZincGrammar.is_whitespace(self.reader.cur):
            self.reader.consume(None, True)

        # If there can not be read any more tokens, simply return None.
        if self.reader.cur is None:
            return None

        if ZincGrammar.is_id_start(self.reader.cur):
            return self.next_identifier()
        elif ZincGrammar.is_keyword_start(self.reader.cur):
            return self.next_keyword()
        elif ZincGrammar.is_symbol_start(self.reader.cur):
            return self.next_symbol()
        elif ZincGrammar.is_ref_start(self.reader.cur):
            return self.next_ref()
        elif ZincGrammar.is_str_start(self.reader.cur):
            return self.next_str()
        elif ZincGrammar.is_uri_start(self.reader.cur):
            return self.next_uri()
        elif ZincGrammar.is_digit(self.reader.cur) or self.reader.cur == "-":
            return self.next_num()
        elif self.reader.peek is not None:
            if self.reader.cur == "<" and self.reader.peek == "<":
                self.reader.consume("<")
                self.reader.consume("<")
                return self.reader.extract_token(ZincTokenType.GRID_START)
            elif self.reader.cur == ">" and self.reader.peek == ">":
                self.reader.consume(">")
                self.reader.consume(">")
                return self.reader.extract_token(ZincTokenType.GRID_END)
            elif self.reader.cur == "\r" and self.reader.peek == "\n":
                self.reader.consume("\r")
                self.reader.consume("\n")
                return self.reader.extract_token(ZincTokenType.LINEFEED)

        # Handle the trivial tokens.
        token_type: ZincTokenType | None = TRIVIAL_TOKEN_TABLE[self.reader.cur]
        if token_type is not None:
            self.reader.consume()
            return self.reader.extract_token(token_type)

        raise Tokenizer.ParseException(f"Unexpected char '{self.reader.cur}'")

