from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Iterator, List


@dataclass(frozen=True)
class AuthMsg:
    @staticmethod
    def make(scheme: str, params: Dict[str, str]) -> AuthMsg:
        return AuthMsg(scheme, params)

    @staticmethod
    def decode(encoded: str) -> AuthMsg:
        encoded_param_list: Iterator[str]

        schema, encoded_params = encoded.split(" ", 1)

        encoded_param_list = map(lambda x: x.strip(" "), encoded_params.split(","))
        params: Dict[str, str] = {}

        for encoded_param in encoded_param_list:
            encoded_key, encoded_value = encoded_param.split("=")

            key = encoded_key.strip().lower()
            value = encoded_value.strip()

            params[key] = value

        return AuthMsg(schema, params)

    scheme: str
    params: Dict[str, str]

    def encode(self) -> str:
        encoded_param_list: List[str] = []
        for key, value in self.params.items():
            encoded_param_list.append(f"{key.lower()}={value}")

        encoded_params: str = ", ".join(encoded_param_list)
        return f"{self.scheme} {encoded_params}"
