from __future__ import annotations

from typing import Dict, List


class MessageParameters(Dict[str, str]):
    @staticmethod
    def decode(encoded: str) -> MessageParameters:
        result: MessageParameters = MessageParameters()

        pairs: List[str] = encoded.split(",")

        for pair in pairs:
            key, value = pair.split("=")
            key = key.strip(' ')
            value = value.strip(' ')
            result[key] = value

        return result

    def __setitem__(self, key: str, value: str, /) -> None:
        return super().__setitem__(key.lower(), value)

    def __getitem__(self, key: str, /) -> str:
        return super().__getitem__(key.lower())
    
    def encode(self) -> str:
        pairs: List[str] = []

        for key, value in self.items():
            pairs.append(f"{key.lower()}={value}")

        return ", ".join(pairs)
