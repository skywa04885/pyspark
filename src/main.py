import asyncio
import aiofiles
import pprint
from typing import AsyncGenerator

from hgrid_transformers import HGridTransformers
from zinc.parser import ZincParser
from ztypes import HZincReader
from zinc.lexer import ZincLexer
from zinc.token import ZincToken, ZincTokenType
from helpers.chunked_iterator_wrapper import ChunkedIteratorWrapper


async def main():
    async with aiofiles.open("../data/defs.zinc") as t:
        a = await ZincParser.parse_root(
            await ZincParser.Context.make(
                ZincLexer.tokenize(
                    await ZincLexer.Context.make(aiter(ChunkedIteratorWrapper(t)))
                )
            ),
            HZincReader(),
        )
        print(HGridTransformers.into_dataframe(a))


asyncio.run(main())
