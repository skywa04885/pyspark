from abc import ABC

from auth.headers.message_parameters import MessageParameters
from helpers.unpadded_base64 import unpadded_base64_encode

from .skyspark_auth_header import SkysparkAuthHeader


class SkysparkAuthHeaderFactory(ABC):
    @staticmethod
    def create_hello(username: str) -> SkysparkAuthHeader:
        params = MessageParameters({"username": unpadded_base64_encode(username)})
        return SkysparkAuthHeader("hello", params)

    @staticmethod
    def create_scram(handshake_token: str, data: str) -> SkysparkAuthHeader:
        params = MessageParameters(
            {"handshakeToken": handshake_token, "data": unpadded_base64_encode(data)}
        )
        return SkysparkAuthHeader("scram", params)

    @staticmethod
    def create_auth(auth_token: str) -> SkysparkAuthHeader:
        params = MessageParameters({"authToken": auth_token})
        return SkysparkAuthHeader("bearer", params)
