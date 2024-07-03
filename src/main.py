import asyncio
import logging
from pprint import pprint
import pandas as pd

from client.client import Client
from haystack.converters.to_dict import haystack_grid_to_dict


async def main():
    logging.basicConfig(level=logging.DEBUG)

    async with Client("vts_transport") as client:
        await client.authenticate("Luke_Rieff", "Ffeir234@ommnia")
        pprint(pd.DataFrame(haystack_grid_to_dict(await client.eval("readAll(his).hisRead(null)"))))

asyncio.run(main())
