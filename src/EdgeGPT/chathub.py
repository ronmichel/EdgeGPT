import asyncio
import json
import os
import ssl
import sys
from time import time
from tkinter import NO
from typing import Generator, List, Union, Optional, Tuple

import aiohttp
import certifi
import httpx
from curl_cffi import requests
from curl_cffi.requests.websockets import WebSocket
from curl_cffi.const import CurlWsFlag
from curl_cffi import AsyncCurl
import urllib
from BingImageCreator import ImageGenAsync

from .constants import DELIMITER, PERSONATE
from .constants import HEADERS
from .constants import HEADERS_INIT_CONVER
from .conversation import Conversation
from .conversation_style import CONVERSATION_STYLE_TYPE, Persona
from .plugin import Plugin
from .request import ChatHubRequest
from .utilities import append_identifier
from .utilities import get_ran_hex
from .utilities import guess_locale


# ssl_context = ssl.create_default_context()
# ssl_context.load_verify_locations(certifi.where())


class ChatHub:
    def __init__(
            self,
            conversation: Conversation,
            proxy: str = None,
            cookies: Union[List[dict], None] = None,
    ) -> None:
        conversationSignature = conversation.struct.get("conversationSignature") or None
        self.aio_session = None
        self.request: ChatHubRequest
        self.loop: bool
        self.task: asyncio.Task
        self.request = ChatHubRequest(
            conversation_signature=conversationSignature,
            client_id=conversation.struct["clientId"],
            conversation_id=conversation.struct["conversationId"],
        )
        self.sec_access_token = conversation.struct["secAccessToken"] or None
        self.cookies = cookies
        self.proxy: str = proxy
        proxy = (
                proxy
                or os.environ.get("all_proxy")
                or os.environ.get("ALL_PROXY")
                or os.environ.get("https_proxy")
                or os.environ.get("HTTPS_PROXY")
                or None
        )
        if proxy is not None and proxy.startswith("socks5h://"):
            proxy = "socks5://" + proxy[len("socks5h://"):]
        self.session = AsyncSession(
            proxy=proxy,
            timeout=900,
            headers=HEADERS_INIT_CONVER,
            impersonate=PERSONATE
        )

    async def get_conversation(
            self,
            conversation_id: str = None,
            conversation_signature: str = None,
            client_id: str = None,
    ) -> dict:
        conversation_id = conversation_id or self.request.conversation_id
        conversation_signature = (
                conversation_signature or self.request.conversation_signature
        )
        client_id = client_id or self.request.client_id
        url = f"https://sydney.bing.com/sydney/GetConversation?conversationId={conversation_id}&source=cib&participantId={client_id}&conversationSignature={conversation_signature}&traceId={get_ran_hex()}"
        response = await self.session.get(url)
        return response.json()

    async def get_activity(self) -> dict:
        url = "https://www.bing.com/turing/conversation/chats"
        headers = HEADERS_INIT_CONVER.copy()
        if self.cookies is not None:
            for cookie in self.cookies:
                if cookie["name"] == "_U":
                    headers["Cookie"] = f"SUID=A; _U={cookie['value']};"
                    break
        response = await self.session.get(url, headers=headers)
        return response.json()

    async def ask_stream(
            self,
            prompt: str,
            wss_link: str = None,
            conversation_style: CONVERSATION_STYLE_TYPE = None,
            raw: bool = False,
            webpage_context: Union[str, None] = None,
            search_result: bool = False,
            locale: str = guess_locale(),
            mode: str = None,
            no_search: bool = True,
            persona: Persona = Persona.copilot,
            plugins: set[Plugin] = {}
    ) -> Generator[bool, Union[dict, str], None]:
        """ """
        cookies = {}
        if self.cookies is not None:
            for cookie in self.cookies:
                cookies[cookie["name"]] = cookie["value"]
        # self.aio_session = aiohttp.ClientSession(cookies=cookies)
        self.aio_session = AsyncSession(
            cookies=cookies,
            headers=HEADERS,
            proxy=self.proxy,
            impersonate=PERSONATE
        )
        token = urllib.parse.quote_plus(self.sec_access_token) if self.sec_access_token else ''
        wss_link = f'{wss_link}?sec_access_token={token}'
        # Check if websocket is closed
        wss = await self.aio_session.ws_connect(wss_link or "wss://sydney.bing.com/sydney/ChatHub")
        await self._initial_handshake(wss)
        # Construct a ChatHub request
        self.request.update(
            prompt=prompt,
            conversation_style=conversation_style,
            webpage_context=webpage_context,
            search_result=search_result,
            locale=locale,
            mode=mode,
            no_search=no_search,
            persona=persona,
            plugins=plugins
        )
        # Send request
        await wss.asend(append_identifier(self.request.struct).encode("utf-8"))
        draw = False
        resp_txt = ""
        result_text = ""
        resp_txt_no_link = ""
        async for obj in self._receive_messages(wss):
            if int(time()) % 6 == 0:
                await wss.asend(append_identifier({"type": 6}).encode("utf-8"))

            if obj is None or not obj:
                continue

            response = json.loads(obj)
            if response.get("type") == 1 and response["arguments"][0].get(
                    "messages",
            ):
                if not draw:
                    msg_type = response["arguments"][0]["messages"][0].get("messageType")
                    if msg_type == "GenerateContentQuery":
                        try:
                            async with ImageGenAsync(
                                    all_cookies=self.cookies,
                            ) as image_generator:
                                images = await image_generator.get_images(
                                    response["arguments"][0]["messages"][0]["text"],
                                )
                            for i, image in enumerate(images):
                                resp_txt = f"{resp_txt}\n![image{i}]({image})"
                            draw = True
                        except Exception as e:
                            print(e)
                            continue
                    if (
                            (
                                    response["arguments"][0]["messages"][0]["contentOrigin"]
                                    != "Apology"
                            )
                            and not draw
                            and not raw
                    ):
                        body = response["arguments"][0]["messages"][0]["adaptiveCards"][0]["body"][0]
                        resp_txt = result_text + body.get("text", "")
                        resp_txt_no_link = result_text + response["arguments"][0][
                            "messages"
                        ][0].get("text", "")
                        if msg_type and "inlines" in body:
                            resp_txt = (
                                    resp_txt
                                    + body["inlines"][0].get("text")
                                    + "\n"
                            )
                            result_text = (
                                    result_text
                                    + response["arguments"][0]["messages"][0][
                                        "adaptiveCards"
                                    ][0]["body"][0]["inlines"][0].get("text")
                                    + "\n"
                            )
                    if not raw:
                        yield False, resp_txt

            elif response.get("type") == 2:
                if response["item"]["result"].get("error"):
                    await self.close()
                    raise Exception(
                        f"{response['item']['result']['value']}: {response['item']['result']['message']}",
                    )
                if draw:
                    cache = response["item"]["messages"][1]["adaptiveCards"][0][
                        "body"
                    ][0]["text"]
                    response["item"]["messages"][1]["adaptiveCards"][0]["body"][0][
                        "text"
                    ] = (cache + resp_txt)
                if (
                        response["item"]["messages"][-1]["contentOrigin"] == "Apology"
                        and resp_txt
                ):
                    response["item"]["messages"][-1]["text"] = resp_txt_no_link
                    response["item"]["messages"][-1]["adaptiveCards"][0]["body"][0][
                        "text"
                    ] = resp_txt
                    print(
                        "Preserved the message from being deleted",
                        file=sys.stderr,
                    )
                wss.close()
                if not self.aio_session.is_closed():
                    await self.aio_session.close()
                yield True, response
                return
            if response.get("type") != 2:
                if response.get("type") == 6:
                    await wss.asend(append_identifier({"type": 6}).encode("utf-8"))
                elif response.get("type") == 7:
                    await wss.asend(append_identifier({"type": 7}).encode("utf-8"))
                elif raw:
                    yield False, response

    async def _initial_handshake(self, wss) -> None:
        proto = append_identifier({"protocol": "json", "version": 1})
        await wss.asend(proto.encode("utf-8"))
        await wss.arecv()
        await wss.asend(append_identifier({"type": 6}).encode("utf8"))

    async def _receive_messages(self, wss: WebSocket) -> Generator[str, Tuple[bytes, int], None]:
        buffer = b''
        retry_count = 5
        is_connected = True
        while is_connected:
            # Receive the next chunk of data
            chunk, flags = await wss.arecv()

            if flags & CurlWsFlag.CLOSE:
                is_connected = False

            if not chunk:
                retry_count -= 1
                if retry_count == 0:
                    raise Exception("No response from server")
                continue

            buffer += chunk
            # Split the buffer by the delimiter
            while b'\x1e' in buffer:
                delimiter_index = buffer.index(b'\x1e')
                # Extract the complete message up to the delimiter
                complete_message = buffer[:delimiter_index]
                yield complete_message.decode('utf-8')
                # Remove the processed message from the buffer
                buffer = buffer[delimiter_index + 1:]

    async def delete_conversation(
            self,
            conversation_id: str = None,
            conversation_signature: str = None,
            client_id: str = None,
    ) -> None:
        conversation_id = conversation_id or self.request.conversation_id
        conversation_signature = (
                conversation_signature or self.request.conversation_signature
        )
        client_id = client_id or self.request.client_id
        url = "https://sydney.bing.com/sydney/DeleteSingleConversation"
        await self.session.post(
            url,
            json={
                "conversationId": conversation_id,
                "conversationSignature": conversation_signature,
                "participant": {"id": client_id},
                "source": "cib",
                "optionsSets": ["autosave"],
            },
        )

    async def close(self) -> None:
        await self.session.close()


class AsyncSession(requests.AsyncSession):
    def __init__(
            self,
            *,
            loop=None,
            async_curl: Optional[AsyncCurl] = None,
            max_clients: int = 10,
            **kwargs,
    ):
        super().__init__(loop=loop, async_curl=async_curl, max_clients=max_clients, **kwargs)

    def is_closed(self):
        return self._closed
