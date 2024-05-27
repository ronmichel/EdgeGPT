import asyncio
import base64
import json
import os
from time import time
from typing import Generator, List, Union, Optional, Tuple

from curl_cffi import requests
from curl_cffi.requests.websockets import WebSocket
from curl_cffi.const import CurlWsFlag
from curl_cffi import AsyncCurl
from curl_cffi.curl import CurlMime
import urllib
from BingImageCreator import ImageGenAsync

from .constants import PERSONATE
from .constants import HEADERS, HEADERS_INIT_CONVER, CONVERSATION_URL
from .conversation import Conversation
from .conversation_style import CONVERSATION_STYLE_TYPE, Persona
from .plugin import Plugin
from .request import ChatHubRequest
from .utilities import append_identifier
from .utilities import get_ran_hex
from .utilities import guess_locale
from .utilities import parse_search_result


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
        url = CONVERSATION_URL.format(
            conversation_id=conversation_id,
            signature=conversation_signature,
            client_id=client_id,
            trace_id=get_ran_hex(),
        )
        # url = f"https://sydney.bing.com/sydney/GetConversation?conversationId={conversation_id}
        # &source=cib&participantId={client_id}&conversationSignature={conversation_signature}&traceId={get_ran_hex()}"
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
        "%s_%s_%s_%s".format()
        return response.json()

    async def ask_stream(
            self,
            prompt: str,
            wss_link: str = None,
            conversation_style: CONVERSATION_STYLE_TYPE = None,
            raw: bool = False,
            webpage_context: Union[str, None] = None,
            locale: str = guess_locale(),
            no_search: bool = True,
            persona: Persona = Persona.copilot,
            plugins: set[Plugin] = {},
            image_url: str = None,
    ) -> Generator[bool, Union[dict, str], None]:
        """ """
        if (not prompt) and (not image_url):
            raise ValueError("prompt or image_url must be provided")

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
            locale=locale,
            no_search=no_search,
            persona=persona,
            plugins=plugins,
            image_url=image_url,
        )
        # Send request
        await wss.asend(append_identifier(self.request.struct).encode("utf-8"))
        prefix_txt = ""
        generate = None
        search_refs = []
        search_keywords = []
        async for obj in self._receive_messages(wss):
            if int(time()) % 6 == 0:
                await wss.asend(append_identifier({"type": 6}).encode("utf-8"))

            if obj is None or not obj:
                continue

            response = json.loads(obj)
            r_type = response.get("type")
            if r_type in [6, 7]:
                await wss.asend(append_identifier({"type": r_type}).encode("utf-8"))

            if raw:
                done = r_type == 2
                yield done, response
                if not done:
                    continue
                else:
                    break

            if r_type == 1 and response["arguments"][0].get(
                    "messages",
            ):
                message = response["arguments"][0]["messages"][0]
                msg_type = message.get("messageType")
                hidden_text = message.get("hiddenText")
                text = message.get("text")
                if msg_type == "InternalSearchQuery":
                    search_keywords.append(hidden_text)
                elif msg_type == "InternalSearchResult":
                    search_refs += parse_search_result(message)
                elif msg_type == "GenerateContentQuery":
                    generate = {
                        "content_type": message.get("contentType"),
                        "prompt": text
                    }
                elif msg_type is None:
                    if message.get("contentOrigin") == "Apology":
                        print('message has been revoked')
                        print(message)
                        prefix_txt = f"{prefix_txt}{text} -end- (message has been revoked)"

                    if len(search_keywords) > 0:
                        keywords = "\n* ".join(search_keywords)
                        prefix_txt = f"{prefix_txt}Searching the web for:\n* {keywords}\n\n"
                        search_keywords = []

                    yield False, f"{prefix_txt}{text}"
            elif response.get("type") == 2:
                if response["item"]["result"].get("error"):
                    raise Exception(
                        f"{response['item']['result']['value']}: {response['item']['result']['message']}",
                    )

                response["media"] = {}
                message = response["item"]["messages"][-1]
                text = message.get("text")
                if generate:
                    if generate["content_type"] == "IMAGE":
                        async with ImageGenAsync(
                                all_cookies=self.cookies,
                                proxy=self.proxy
                        ) as image_obj:
                            try:
                                images = await image_obj.get_images(generate["prompt"])
                                response["media"] = {
                                    "prompt": generate["prompt"],
                                    "images": images
                                }
                            except Exception as e:
                                print(str(e))
                                hint = "Your prompt has been prohibited by third-service. Please modify it."
                                prefix_txt = f"{prefix_txt}{text}\n{e}\n{hint}"

                if len(search_refs) > 0:
                    refs_str = ""
                    for index, item in enumerate(search_refs):
                        refs_str += f'- [^{index}^] [{item["title"]}]({item["url"]})\n'

                    message["text"] = f"{prefix_txt}{text}\n{refs_str}"
                else:
                    message["text"] = f"{prefix_txt}{text}"

                if "media" not in response:
                    response["media"] = {}

                yield True, response
                return

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

        return

    async def delete_conversation(
            self,
            conversation_id: str = None,
            conversation_signature: str = None,
            client_id: str = None,
    ) -> None:
        conversation_id = conversation_id or self.conversation_id
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

    async def upload_image(
            self,
            binary_image: bytes,
            style: CONVERSATION_STYLE_TYPE = "precise",
            blur: bool = False
    ) -> dict:
        if not isinstance(style, str):
            style = style.name

        url = "https://www.bing.com/images/kblob"
        payload = {
            "imageInfo": {},
            "knowledgeRequest": {
                "invokedSkills": ["ImageById"],
                "subscriptionId": "Bing.Chat.Multimodal",
                "invokedSkillsRequestData": {"enableFaceBlur": blur},
                "convoData": {
                    "convoid": "",
                    "convotone": style,
                }
            }
        }
        encode_data = base64.b64encode(binary_image)

        parts = CurlMime()
        parts.addpart(
            name="knowledgeRequest",
            content_type="application/json",
            data=json.dumps(payload).encode("utf-8"),
        )
        parts.addpart(
            name="imageBase64",
            content_type="application/octet-stream",
            data=encode_data,
        )

        async with AsyncSession(
            headers={
                "Referer": "https://www.bing.com/search?q=Bing+AI&showconv=1&FORM=hpcodx"
            },
            proxy=self.proxy,
            impersonate=PERSONATE,
            timeout=900,
        ) as session:
            resp = await session.post(url, multipart=parts)
            if not resp.ok:
                raise Exception(f"Failed to upload image. Status: {resp.status}")

            return resp.json()


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

    async def close(self) -> None:
        if not self._closed:
            await super().close()
