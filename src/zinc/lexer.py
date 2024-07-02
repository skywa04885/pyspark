from __future__ import annotations
from dataclasses import dataclass
from typing import (
    AsyncGenerator,
    AsyncIterator,
    Callable,
    ClassVar,
    Dict,
    Generator,
    List,
    Optional,
    Tuple,
)

from .grammer import ZincGrammar
from .token import ZincToken, ZincTokenType

Tester = Callable[[str], bool]


class ZincLexer:
    _TRIVIAL_TOKEN_TABLE: ClassVar[Dict[str, ZincTokenType]] = {
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
    class LexicalError(Exception):
        message: Optional[str] = None

    @dataclass
    class Context:
        @staticmethod
        async def make(it: AsyncIterator[str]) -> ZincLexer.Context:
            current: Optional[str] = await anext(it, None)
            peek: Optional[str] = await anext(it, None)

            return ZincLexer.Context(it, current, peek)

        it: AsyncIterator[str]

        current: Optional[str]
        peek: Optional[str]

        async def next(self) -> None:
            self.current = self.peek
            self.peek = await anext(self.it, None)

        async def consume(
            self, tester: Optional[Tester] = None, segments: Optional[List[str]] = None
        ) -> None:
            if self.current is None:
                raise ZincLexer.LexicalError("Unexpected end")

            if tester is not None and not tester(self.current):
                raise ZincLexer.LexicalError("Unexpected character")

            if segments is not None:
                segments.append(self.current)

            await self.next()

        async def consume_if(
            self, tester: Tester, segments: Optional[List[str]] = None
        ) -> bool:
            if self.current is None:
                return False

            if not tester(self.current):
                return False

            if segments is not None:
                segments.append(self.current)

            await self.next()

            return True

        async def current_is(self, tester: Tester) -> bool:
            if self.current is None:
                return False

            return tester(self.current)

    @staticmethod
    async def vomit_whitespace(context: Context) -> None:
        while await context.consume_if(ZincGrammar.is_whitespace):
            pass

    @staticmethod
    async def _consume_identifier(
        context: Context, segments: List[str]
    ) -> ZincTokenType:
        while await context.consume_if(ZincGrammar.is_id_part, segments):
            pass

        return ZincTokenType.IDENTIFIER

    @staticmethod
    async def _consume_keyword(context: Context, segments: List[str]) -> ZincTokenType:
        while await context.consume_if(ZincGrammar.is_keyword_part, segments):
            pass

        return ZincTokenType.KEYWORD

    @staticmethod
    async def _consume_symbol(context: Context, segments: List[str]) -> ZincTokenType:
        while await context.consume_if(ZincGrammar.is_symbol_part, segments):
            pass

        return ZincTokenType.SYMBOL

    @staticmethod
    async def _consume_ref(context: Context, segments: List[str]) -> ZincTokenType:
        while await context.consume_if(ZincGrammar.is_ref_part, segments):
            pass

        await context.consume_if(ZincGrammar.is_ref_end, segments)

        return ZincTokenType.REF

    @staticmethod
    async def _consume_str(context: Context, segments: List[str]) -> ZincTokenType:
        while True:
            if context.current is None:
                raise ZincLexer.LexicalError("String not terminated")

            if await context.consume_if(ZincGrammar.is_str_escape, segments):
                if await context.consume_if(ZincGrammar.is_str_escaped_char, segments):
                    continue
                elif await context.consume_if(ZincGrammar.is_str_escped_uni, segments):
                    for _ in range(0, 4):
                        await context.consume(ZincGrammar.is_hex_digit, segments)
                else:
                    raise ZincLexer.LexicalError(f"Expected escaped character.")
            elif await context.consume_if(ZincGrammar.is_str_end, segments):
                break
            elif await context.consume_if(ZincGrammar.is_unicode_char, segments):
                pass
            else:
                raise ZincLexer.LexicalError(
                    f"Invalid character in string: '{context.current}'"
                )

        return ZincTokenType.STR

    @staticmethod
    async def _consume_uri(context: Context, segments: List[str]) -> ZincTokenType:
        while True:
            if context.current is None:
                raise ZincLexer.LexicalError("URI not terminated")

            if await context.consume_if(ZincGrammar.is_uri_escape, segments):
                if await context.consume_if(ZincGrammar.is_uri_escaped_char, segments):
                    continue
                elif await context.consume_if(ZincGrammar.is_uri_escaped_uni, segments):
                    for _ in range(0, 4):
                        await context.consume(ZincGrammar.is_hex_digit, segments)
                else:
                    raise ZincLexer.LexicalError(f"Expected escaped character.")
            elif await context.consume_if(ZincGrammar.is_uri_end, segments):
                break
            elif await context.consume_if(ZincGrammar.is_unicode_char, segments):
                pass
            else:
                raise ZincLexer.LexicalError(
                    f"Invalid character in URI: '{context.current}'"
                )

        return ZincTokenType.URI

    @staticmethod
    async def _consume_number(context: Context, segments: List[str]) -> ZincTokenType:
        colons: int = 0
        dashes: int = 0
        unit_found: bool = False
        exp: bool = False

        while context.current is not None:
            if ZincGrammar.is_digit(context.current):
                await context.consume(None, segments)
                continue
            elif exp and context.current in ["+", "-"]:
                pass
            elif context.current == "-":
                dashes += 1
            elif (
                context.current == ":"
                and context.peek is not None
                and ZincGrammar.is_digit(context.peek)
            ):
                colons += 1
            elif (exp or colons >= 1) and context.current == "+":
                pass
            elif context.current == ".":
                if context.peek is None or not ZincGrammar.is_digit(context.peek):
                    break
            elif (
                context.current in ["e", "E"]
                and context.peek is not None
                and (context.peek in ["-", "+"] or ZincGrammar.is_digit(context.peek))
            ):
                exp = True
            elif (
                ZincGrammar.is_alpha(context.current)
                or context.current in ["%", "$", "/"]
                or ord(context.current) > 128
            ):
                unit_found = True
            elif context.current == "_":
                if unit_found and ZincGrammar.is_digit(context.current):
                    await context.consume(None, segments)
                    continue
                else:
                    unit_found = True
            else:
                break

            await context.consume(None, segments)

        if dashes == 2 and colons == 0:
            return ZincTokenType.DATE
        elif dashes == 0 and colons > 1:
            return ZincTokenType.TIME
        elif dashes > 2:
            return ZincTokenType.DATETIME

        return ZincTokenType.NUMBER

    @staticmethod
    async def tokenize(context: Context) -> AsyncGenerator[ZincToken, None]:
        while context.current is not None:
            await ZincLexer.vomit_whitespace(context)

            if context.current is None:
                break

            segments: List[str] = []
            token_type: Optional[ZincTokenType] = None

            if await context.consume_if(ZincGrammar.is_id_start, segments):
                token_type = await ZincLexer._consume_identifier(context, segments)
            elif await context.consume_if(ZincGrammar.is_keyword_start, segments):
                token_type = await ZincLexer._consume_keyword(context, segments)
            elif await context.consume_if(ZincGrammar.is_symbol_start, segments):
                token_type = await ZincLexer._consume_symbol(context, segments)
            elif await context.consume_if(ZincGrammar.is_ref_start, segments):
                token_type = await ZincLexer._consume_ref(context, segments)
            elif await context.consume_if(ZincGrammar.is_str_start, segments):
                token_type = await ZincLexer._consume_str(context, segments)
            elif await context.consume_if(ZincGrammar.is_uri_start, segments):
                token_type = await ZincLexer._consume_uri(context, segments)
            elif await context.consume_if(ZincGrammar.is_number_start, segments):
                token_type = await ZincLexer._consume_number(context, segments)
            elif context.current == "<" and context.peek == "<":
                await context.consume(None, segments)
                await context.consume(None, segments)
                token_type = ZincTokenType.GRID_START
            elif context.current == ">" and context.peek == ">":
                await context.consume(None, segments)
                await context.consume(None, segments)
                token_type = ZincTokenType.GRID_START
            
            if token_type is None:
                token_type = ZincLexer._TRIVIAL_TOKEN_TABLE.get(context.current)
                await context.consume(None, segments)

            if token_type is not None:
                yield ZincToken(token_type, "".join(segments))
            else:
                raise ZincLexer.LexicalError(f"Unexpected char: {context.current}")
