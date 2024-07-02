import asyncio
import aiofiles
import pprint
from typing import AsyncGenerator

from zinc.parser import ZincParser
from ztypes import HZincReader
from zinc.lexer import ChunkedIteratorWrapper, ZincLexer
from zinc.token import ZincToken, ZincTokenType

async def main():
    async with aiofiles.open("../data/defs.zinc") as t:
       a = await ZincParser.parse_root(await ZincParser.Context.make(ZincLexer.tokenize(await ZincLexer.Context.make(aiter(ChunkedIteratorWrapper(t))))), HZincReader())
       print(a)

asyncio.run(main())
