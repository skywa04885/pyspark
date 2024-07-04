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

    async def authenticate(self, username: str, password: str) -> None:

        self.logger.debug(
            f"Sending hello for username '{username}' and password '{password}'"
        )

        # Hello message
        async with self.session.get(
            f"{self.api_path}/about",
            headers={
                "Authorization": SkysparkAuthHeaderFactory.create_hello(
                    username
                ).encode()
            },
        ) as response:
            if response.status != 401:
                raise Client.AuthenticationError(
                    f"Expected status code 401, got {response.status}"
                )

            www_authenticate: Optional[str] = response.headers.get("WWW-Authenticate")

            if www_authenticate is None:
                raise Client.AuthenticationError(
                    f"Missing authentication header 'WWW-Authenticate'"
                )

            recv_auth_msg: SkysparkAuthHeader = SkysparkAuthHeader.decode(
                www_authenticate
            )

        if recv_auth_msg.schema != "scram":
            raise Client.AuthenticationError(
                f"Unsupported authentication scheme {recv_auth_msg.schema}"
            )

        print(recv_auth_msg.params)
        handshake_token: str = recv_auth_msg.params["handshaketoken"]
        auth_hash_algo: str = recv_auth_msg.params["hash"]

        # Prep mech.
        mechanisms: List[str] = []
        if auth_hash_algo == "SHA-256":
            mechanisms.append("SCRAM-SHA-256")
        elif auth_hash_algo == "SHA-512":
            mechanisms.append("SCRAM-SHA-512")
        else:
            raise Client.AuthenticationError(
                f"Unsupported hashing algorithm {auth_hash_algo}"
            )

        # Scram create client
        scram_client: ScramClient = ScramClient(mechanisms, username, password)

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

            www_authenticate: Optional[str] = response.headers.get("WWW-Authenticate")

            if www_authenticate is None:
                raise Client.AuthenticationError(
                    f"Missing authentication header 'WWW-Authenticate' after client first"
                )

            recv_auth_msg: SkysparkAuthHeader = SkysparkAuthHeader.decode(
                www_authenticate
            )

        handshake_token: str = recv_auth_msg.params["handshaketoken"]
        data: str = recv_auth_msg.params["data"]

        ##### STEP 2

        scram_client.set_server_first(
            urlsafe_b64decode((data + "=" * (len(data) % 4)).encode()).decode()
        )

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

            authentication_info: str = response.headers["Authentication-Info"]

            params = MessageParameters.decode(authentication_info)

        auth_token: str = params["authtoken"]
        data: str = params["data"]

        ##### STEP 3

        try:
            scram_client.set_server_final(
                urlsafe_b64decode((data + "=" * (len(data) % 4)).encode()).decode()
            )
        except ScramException:
            raise Client.AuthenticationError("Authenticatio failed")

        self.logger.debug("Logged in")

        self.session.headers.add(
            "Authorization",
            SkysparkAuthHeaderFactory.create_auth(auth_token).encode(),
        )
