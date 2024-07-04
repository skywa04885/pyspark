from __future__ import annotations
from dataclasses import dataclass

from helpers.unpadded_base64 import unpadded_base64_decode

from .message_parameters import MessageParameters


@dataclass(frozen=True)
class SkysparkAuthHeader:
    schema: str
    params: MessageParameters

    @staticmethod
    def decode(raw: str) -> SkysparkAuthHeader:
        schema, remainder = raw.split(" ", 1)
        params = MessageParameters.decode(remainder)

        return SkysparkAuthHeader(schema, params)
    
    def encode(self) -> str:
        return f"{self.schema} {self.params.encode()}"
