from __future__ import annotations
from contextlib import AbstractAsyncContextManager
from email import parser
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from aiohttp import ClientSession
from base64 import urlsafe_b64encode, urlsafe_b64decode
from pprint import pprint
from scramp import ScramClient, ScramException
import logging

from helpers.chunked_iterator_wrapper import ChunkedIteratorWrapper
from auth.headers.skyspark_auth_header import SkysparkAuthHeader
from auth.headers.skyspark_auth_header_factory import SkysparkAuthHeaderFactory
from auth.headers.message_parameters import MessageParameters
from helpers.unpadded_base64 import unpadded_base64_decode
from zinc.parser import ZincParser
from zinc.lexer import ZincLexer
from ztypes import HGrid, HZincReader


class Client(AbstractAsyncContextManager):
    @dataclass(frozen=True)
    class AuthenticationError(Exception):
        message: Optional[str]

    project: str
    session: ClientSession
    logger: logging.Logger

    def __init__(self, project: str) -> None:
        self.project = project
        self.session = ClientSession(base_url="https://test.skyspark01.ommnia.nl/")
        self.logger = logging.getLogger(__name__)

    async def __aenter__(self) -> Client:
        await self.session.__aenter__()

        return self

    async def __aexit__(self, *kwargs) -> None:
        await self.session.__aexit__(*kwargs)

        return None

    @property
    def api_path(self) -> str:
        return f"/api/{self.project}"

    async def eval(self, expr: str) -> HGrid:
        # Create the path and the parameters.
        path: str = f"{self.api_path}/eval"
        params: Dict[str, Any] = {"expr": expr}

        # Perform the evaluation request.
        async with self.session.get(path, params=params) as response:
            # Turn the chunked response content into a character iterator.
            chunk_iter = response.content.iter_chunked(1024)
            char_iter = ChunkedIteratorWrapper(chunk_iter)

            # Create the lexer context then the start tokenizing the stream of chars.
            lexer_ctx = await ZincLexer.Context.make(char_iter)
            token_iter = ZincLexer.tokenize(lexer_ctx)

            # Create the parser context and parse the tokens.
            parser_ctx = await ZincParser.Context.make(token_iter)
            return await ZincParser.parse_root(parser_ctx, HZincReader())

    async def _auth_send_hello(self, username: str) -> Tuple[str, str, str]:
        self.logger.debug(f"Sending hello for username '{username}'")

        path = f"{self.api_path}/about"
        headers = {
            "Authorization": SkysparkAuthHeaderFactory.create_hello(username).encode()
        }

        async with self.session.get(path, headers=headers) as response:
            if response.status != 401:
                raise Client.AuthenticationError(
                    f"Expected status code 401, got {response.status}"
                )

            auth_header = SkysparkAuthHeader.decode(
                response.headers["WWW-Authenticate"]
            )

            schema: str = auth_header.schema
            handshake_token: str = auth_header.params["handshakeToken"]
            hash_: str = auth_header.params["hash"]

            return (schema, handshake_token, hash_)

    def _auth_initialize_scam(
        self, username: str, password: str, hash_: str
    ) -> ScramClient:
        mechanisms: List[str] = []

        match hash_:
            case "SHA-256":
                mechanisms.append("SCRAM-SHA-256")
            case "SHA-512":
                mechanisms.append("SCRAM-SHA-512")
            case _:
                raise Client.AuthenticationError(
                    f"Unsupported hashing algorithm {hash_}"
                )

        return ScramClient(mechanisms, username, password)

    async def authenticate(self, username: str, password: str) -> None:
        (schema, handshake_token, hash_) = await self._auth_send_hello(username)

        if schema != "scram":
            raise Client.AuthenticationError(f"Scheme {schema} not supported")

        scram_client = self._auth_initialize_scam(username, password, hash_)

        self.logger.debug("Sending SCRAM first")

        ## STEP 1

        async with self.session.get(
            f"{self.api_path}/about",
            headers={
                "Authorization": SkysparkAuthHeaderFactory.create_scram(
                    handshake_token, scram_client.get_client_first()
                ).encode(),
            },
        ) as response:
            if response.status != 401:
                raise Client.AuthenticationError(
                    f"Expected status code 401 after client first, got {response.status}"
                )

            recv_auth_msg: SkysparkAuthHeader = SkysparkAuthHeader.decode(
                response.headers["WWW-Authenticate"]
            )

        handshake_token: str = recv_auth_msg.params["handshaketoken"]
        data: str = recv_auth_msg.params["data"]

        ##### STEP 2

        scram_client.set_server_first(unpadded_base64_decode(data))

        ## STEP 3
        self.logger.debug("Sending SCRAM second")

        async with self.session.get(
            f"{self.api_path}/about",
            headers={
                "Authorization": SkysparkAuthHeaderFactory.create_scram(
                    handshake_token, scram_client.get_client_final()
                ).encode(),
            },
        ) as response:
            if response.status != 200:
                raise Client.AuthenticationError(
                    f"Expected status code 200 after client final, got {response.status}"
                )

            params = MessageParameters.decode(response.headers["Authentication-Info"])

        auth_token: str = params["authToken"]
        data: str = params["data"]

        ##### STEP 3

        try:
            scram_client.set_server_final(unpadded_base64_decode(data))
        except ScramException:
            raise Client.AuthenticationError("Authenticatio failed")

        self.logger.debug("Logged in")

        self.session.headers.add(
            "Authorization",
            SkysparkAuthHeaderFactory.create_auth(auth_token).encode(),
        )
