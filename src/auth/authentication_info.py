from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Iterator, List


@dataclass(frozen=True)
class AuthInfo:
    @staticmethod
    def make(params: Dict[str, str]) -> AuthInfo:
        return AuthInfo(params)

    @staticmethod
    def decode(encoded: str) -> AuthInfo:
        encoded_param_list: Iterator[str]

        encoded_param_list = map(lambda x: x.strip(" "), encoded.split(","))
        params: Dict[str, str] = {}

        for encoded_param in encoded_param_list:
            encoded_key, encoded_value = encoded_param.split("=")

            key = encoded_key.strip().lower()
            value = encoded_value.strip()

            params[key] = value

        return AuthInfo(params)

    params: Dict[str, str]
