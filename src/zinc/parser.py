from __future__ import annotations
from typing import Dict, AsyncIterator, List, Tuple
from dataclasses import dataclass

from .token import ZincToken, ZincTokenType
from ztypes import (
    HCol,
    HDate,
    HDateTime,
    HDict,
    HGrid,
    HList,
    HMarker,
    HNa,
    HNull,
    HRef,
    HRemove,
    HRow,
    HStr,
    HSymbol,
    HTime,
    HUri,
    HVal,
    HBool,
    HCoord,
    HNum,
    HXstr,
    HBin,
)
from ztypes import HReader


class ZincParser:
    @dataclass(frozen=True)
    class AssembleError(Exception):
        message: str | None = None

    @dataclass
    class Context:
        @staticmethod
        async def make(it: AsyncIterator[ZincToken]) -> ZincParser.Context:
            cur: ZincToken | None = await anext(it, None)
            peek: ZincToken | None = await anext(it, None)
            return ZincParser.Context(it, cur, peek)

        it: AsyncIterator[ZincToken]
        cur: ZincToken | None
        peek: ZincToken | None

        async def next(self) -> None:
            self.cur = self.peek
            self.peek = await anext(self.it, None)

        async def consume_if(self, t: ZincTokenType, v: str | None = None) -> str | None:
            if self.cur is None:
                return None
            elif self.cur.t != t:
                return None
            elif v is not None and str(self.cur) != v:
                return None

            s: str = str(self.cur)

            await self.next()

            return s

        def current_is(self, t: ZincTokenType, v: str | None = None) -> bool:
            if self.cur is None:
                return False
            elif self.cur.t != t:
                return False
            elif v is not None and str(self.cur) != v:
                return False

            return True

        async def consume(self, t: ZincTokenType, v: str | None = None) -> str:
            if self.cur is None:
                raise ZincParser.AssembleError(f"Unexpected end")
            if self.cur.t != t:
                raise ZincParser.AssembleError(f"Expected {t} got {self.cur.t}")
            if v is not None and str(self.cur) != v:
                raise ZincParser.AssembleError(f"Expected {v} got {str(self.cur)}")

            s: str = str(self.cur)

            await self.next()

            return s

    @staticmethod
    async def parse_ref(context: ZincParser.Context, reader: HReader) -> HRef:
        ref: HRef = reader.read_ref(await context.consume(ZincTokenType.REF))

        if not context.current_is(ZincTokenType.STR):
            return ref

        name: HStr = reader.read_str(await context.consume(ZincTokenType.STR))

        return ref.with_name(name)

    @staticmethod
    async def parse_symbol(context: ZincParser.Context, reader: HReader) -> HSymbol:
        return reader.read_symbol(await context.consume(ZincTokenType.SYMBOL))

    @staticmethod
    async def parse_bool(context: ZincParser.Context, reader: HReader) -> HBool:
        return reader.read_bool(await context.consume(ZincTokenType.BOOL))

    @staticmethod
    async def parse_uri(context: ZincParser.Context, reader: HReader) -> HUri:
        return reader.read_uri(await context.consume(ZincTokenType.URI))

    @staticmethod
    async def parse_str(context: ZincParser.Context, reader: HReader) -> HStr:
        return reader.read_str(await context.consume(ZincTokenType.STR))

    @staticmethod
    async def parse_num(context: ZincParser.Context, reader: HReader) -> HNum:
        return reader.read_num(await context.consume(ZincTokenType.NUMBER))

    @staticmethod
    async def parse_date(context: ZincParser.Context, reader: HReader) -> HDate:
        return reader.read_date(await context.consume(ZincTokenType.DATE))

    @staticmethod
    async def parse_time(context: ZincParser.Context, reader: HReader) -> HTime:
        return reader.read_time(await context.consume(ZincTokenType.TIME))

    @staticmethod
    async def parse_date_time(
        context: ZincParser.Context, reader: HReader
    ) -> HDateTime:
        return reader.read_date_time(await context.consume(ZincTokenType.DATETIME))

    @staticmethod
    async def parse_null(context: ZincParser.Context, reader: HReader) -> HNull:
        await context.consume(ZincTokenType.KEYWORD, "N")
        return HNull.make()

    @staticmethod
    async def parse_marker(context: ZincParser.Context, reader: HReader) -> HMarker:
        await context.consume(ZincTokenType.KEYWORD, "M")
        return HMarker.make()

    @staticmethod
    async def parse_remove(context: ZincParser.Context, reader: HReader) -> HRemove:
        await context.consume(ZincTokenType.KEYWORD, "R")
        return HRemove.make()

    @staticmethod
    async def parse_na(context: ZincParser.Context, reader: HReader) -> HNa:
        await context.consume(ZincTokenType.KEYWORD, "NA")
        return HNa.make()

    @staticmethod
    async def parse_coord(context: ZincParser.Context, reader: HReader) -> HCoord:
        await context.consume(ZincTokenType.KEYWORD, "C")
        await context.consume(ZincTokenType.LPAREN)
        lat: HNum = reader.read_num(await context.consume(ZincTokenType.NUMBER))
        await context.consume(ZincTokenType.COLON)
        lon: HNum = reader.read_num(await context.consume(ZincTokenType.NUMBER))
        await context.consume(ZincTokenType.RPAREN)

        return HCoord.make(lat.val, lon.val)

    @staticmethod
    async def parse_xstr(context: ZincParser.Context, reader: HReader) -> HXstr:
        type_: str = await context.consume(ZincTokenType.KEYWORD)
        await context.consume(ZincTokenType.LPAREN)
        str_: HStr = reader.read_str(await context.consume(ZincTokenType.STR))
        await context.consume(ZincTokenType.RPAREN)

        return HXstr.make(type_, str_)

    @staticmethod
    async def parse_list(context: ZincParser.Context, reader: HReader) -> HList:
        await context.consume(ZincTokenType.LBRACKET)

        val: List[HVal] = []

        while True:
            if await context.consume_if(ZincTokenType.RBRACKET) is not None:
                break

            val.append(await ZincParser.parse_literal(context, reader))

            if await context.consume_if(ZincTokenType.COMMA) is not None:
                continue

        return HList.make(val)

    @staticmethod
    async def parse_tag(
        context: ZincParser.Context, reader: HReader
    ) -> Tuple[str, HVal]:
        id_: str = await context.consume(ZincTokenType.IDENTIFIER)

        if await context.consume_if(ZincTokenType.COLON) is None:
            return (id_, HMarker.make())

        val_: HVal = await ZincParser.parse_literal(context, reader)

        return (id_, val_)

    @staticmethod
    async def parse_tags(
        context: ZincParser.Context, reader: HReader, allow_comma: bool = True
    ) -> Dict[str, HVal]:
        tags: Dict[str, HVal] = {}

        while context.current_is(ZincTokenType.IDENTIFIER):
            (id_, val_) = await ZincParser.parse_tag(context, reader)

            tags[id_] = val_

            if allow_comma:
                _ = await context.consume_if(ZincTokenType.COMMA)

        return tags

    @staticmethod
    async def parse_dict(context: ZincParser.Context, reader: HReader) -> HDict:
        _ = await context.consume(ZincTokenType.LBRACE)
        
        tags: Dict[str, HVal] = await ZincParser.parse_tags(context, reader, allow_comma=True)

        _ = await context.consume(ZincTokenType.RBRACE)

        return HDict.make(tags)

    @staticmethod
    async def parse_bin(context: ZincParser.Context, reader: HReader) -> HBin:
        await context.consume(ZincTokenType.KEYWORD, "Bin")
        await context.consume(ZincTokenType.LPAREN)
        mime_type: HStr = reader.read_str(await context.consume(ZincTokenType.STR))
        await context.consume(ZincTokenType.RPAREN)

        return HBin.make(mime_type)

    @staticmethod
    async def parse_col(
        context: ZincParser.Context, reader: HReader, index: int
    ) -> HCol:
        name_: str = await context.consume(ZincTokenType.IDENTIFIER)
        meta_: Dict[str, HVal] = await ZincParser.parse_tags(
            context, reader, allow_comma=False
        )
        return HCol.make(index, name_, meta_)

    @staticmethod
    async def parse_cols(context: ZincParser.Context, reader: HReader) -> List[HCol]:
        cols: List[HCol] = []

        while True:
            cols.append(await ZincParser.parse_col(context, reader, len(cols)))

            if await context.consume_if(ZincTokenType.COMMA) is None:
                break

        await context.consume(ZincTokenType.LINEFEED)

        return cols

    @staticmethod
    async def parse_row(context: ZincParser.Context, reader: HReader) -> HRow:
        cells: List[HVal] = []

        while True:
            if await context.consume_if(ZincTokenType.LINEFEED) is not None:
                cells.append(HNull.make())
                break
            elif await context.consume_if(ZincTokenType.COMMA) is not None:
                cells.append(HNull.make())
                continue
            
            cells.append(await ZincParser.parse_literal(context, reader))

            if await context.consume_if(ZincTokenType.LINEFEED) is not None:
                break

            _ = await context.consume(ZincTokenType.COMMA)
        
        if len(cells) == 0:
            raise ZincParser.AssembleError(f"Row must contain at least one item")

        return HRow.make(cells)

    @staticmethod
    async def parse_grid_ver(context: ZincParser.Context, reader: HReader) -> HStr:
        await context.consume(ZincTokenType.IDENTIFIER, "ver")
        await context.consume(ZincTokenType.COLON)
        return reader.read_str(await context.consume(ZincTokenType.STR))

    @staticmethod
    async def parse_root(context: ZincParser.Context, reader: HReader) -> HGrid:
        ver_: HStr = await ZincParser.parse_grid_ver(context, reader)
        meta_: Dict[str, HVal] = await ZincParser.parse_tags(
            context, reader, allow_comma=False
        )
        await context.consume(ZincTokenType.LINEFEED)

        if ver_.val != "3.0":
            raise ZincParser.AssembleError(
                f"Expected version 3.0 got {ver_.val} instead"
            )

        cols_: List[HCol] = await ZincParser.parse_cols(context, reader)

        rows_: List[HRow] = []

        while context.cur is not None:
            rows_.append(await ZincParser.parse_row(context, reader))

        return HGrid.make(meta_, cols_, rows_)

    @staticmethod
    async def parse_nested_grid(context: ZincParser.Context, reader: HReader) -> HGrid:
        await context.consume(ZincTokenType.GRID_START)

        ver_: HStr = await ZincParser.parse_grid_ver(context, reader)
        meta_: Dict[str, HVal] = await ZincParser.parse_tags(
            context, reader, allow_comma=False
        )
        await context.consume(ZincTokenType.LINEFEED)

        if ver_.val != "3.0":
            raise ZincParser.AssembleError(
                f"Expected version 3.0 got {ver_.val} instead"
            )

        cols_: List[HCol] = await ZincParser.parse_cols(context, reader)

        rows_: List[HRow] = []

        while await context.consume_if(ZincTokenType.GRID_END) is None:
            rows_.append(await ZincParser.parse_row(context, reader))

        return HGrid.make(meta_, cols_, rows_)

    @staticmethod
    async def parse_literal(context: ZincParser.Context, reader: HReader) -> HVal:
        if context.cur is None:
            raise HReader.ReadException(f"Unexpected end")

        # Check the type of literal we have to assemble.
        match (context.cur.t, context.peek.t if context.peek is not None else None):
            ############################################################################
            ## Literals consisting of a keyword and string between parentheses.
            ############################################################################
            case (ZincTokenType.KEYWORD, ZincTokenType.LPAREN) if str(context.cur) == "C":
                return await ZincParser.parse_coord(context, reader)
            case (ZincTokenType.KEYWORD, ZincTokenType.LPAREN) if str(context.cur) == "Bin":
                return await ZincParser.parse_bin(context, reader)
            case (ZincTokenType.KEYWORD, ZincTokenType.LPAREN):
                return await ZincParser.parse_xstr(context, reader)
            ############################################################################
            ## Grid, dict and list literal assembly
            ############################################################################
            case (ZincTokenType.LBRACKET, _):
                return await ZincParser.parse_list(context, reader)
            case (ZincTokenType.LBRACE, _):
                return await ZincParser.parse_dict(context, reader)
            case (ZincTokenType.GRID_START, _):
                return await ZincParser.parse_nested_grid(context, reader)
            ############################################################################
            ## Simple literal assembly
            ############################################################################
            case (ZincTokenType.REF, _):
                return await ZincParser.parse_ref(context, reader)
            case (ZincTokenType.SYMBOL, _):
                return await ZincParser.parse_symbol(context, reader)
            case (ZincTokenType.BOOL, _):
                return await ZincParser.parse_bool(context, reader)
            case (ZincTokenType.URI, _):
                return await ZincParser.parse_uri(context, reader)
            case (ZincTokenType.NUMBER, _):
                return await ZincParser.parse_num(context, reader)
            case (ZincTokenType.STR, _):
                return await ZincParser.parse_str(context, reader)
            case (ZincTokenType.DATE, _):
                return await ZincParser.parse_date(context, reader)
            case (ZincTokenType.TIME, _):
                return await ZincParser.parse_time(context, reader)
            case (ZincTokenType.DATETIME, _):
                return await ZincParser.parse_date_time(context, reader)
            ############################################################################
            ## Simple keyword literal assembly
            ############################################################################
            case (ZincTokenType.KEYWORD, _) if str(context.cur) == "N":
                return await ZincParser.parse_null(context, reader)
            case (ZincTokenType.KEYWORD, _) if str(context.cur) == "M":
                return await ZincParser.parse_marker(context, reader)
            case (ZincTokenType.KEYWORD, _) if str(context.cur) == "R":
                return await ZincParser.parse_remove(context, reader)
            case (ZincTokenType.KEYWORD, _) if str(context.cur) == "NA":
                return await ZincParser.parse_na(context, reader)
            case _:
                raise ZincParser.AssembleError(f"Unexpected token {context.cur.t}")
