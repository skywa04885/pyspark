from __future__ import annotations
from dataclasses import dataclass
from typing import AsyncIterator


@dataclass
class ChunkedIteratorWrapper(AsyncIterator[str]):
    _source: AsyncIterator[str]
    _buffer: str = ""
    _read: int = 0

    async def _fetch(self) -> None:
        self._buffer = self._buffer[self._read :]
        self._read = 0
        self._buffer += await anext(self._source, "")

    async def __anext__(self) -> str:
        # If the buffer is empty, first try to fetch more data.
        if len(self) == 0:
            await self._fetch()

        # If the buffer is still empty, the stream has ended, return None.
        if len(self) == 0:
            raise StopAsyncIteration

        # Read the single char from the buffer.
        c: str = self._buffer[self._read]
        self._read += 1
        return c

    def __aiter__(self) -> ChunkedIteratorWrapper:
        return self

    def __len__(self) -> int:
        return len(self._buffer) - self._read
