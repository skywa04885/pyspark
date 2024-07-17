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
        print(pd.DataFrame(haystack_grid_to_dict(await client.eval("readById(@p:vts_transport:r:2de9c44a-14b1228c).hisRead(2024)"))))

asyncio.run(main())
