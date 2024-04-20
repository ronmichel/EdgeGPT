import json
import os
from typing import List
from typing import Union

from curl_cffi import requests
from curl_cffi.requests import AsyncSession

from .constants import HEADERS_INIT_CONVER
from .exceptions import NotAllowedToAccess


class Conversation:
    def __init__(
        self,
        proxy: Union[str, None] = None,
        async_mode: bool = False,
        cookies: Union[List[dict], None] = None,
    ) -> None:
        if async_mode:
            return
        self.struct: dict = {
            "conversationId": None,
            "clientId": None,
            "conversationSignature": None,
            "secAccessToken": None,
            "result": {"value": "Success", "message": None},
        }
        self.proxy = proxy
        self.session = requests.Session(
            proxy=proxy,
            timeout=900,
            headers=HEADERS_INIT_CONVER,
            impersonate="chrome116"
        )
        if cookies:
            for cookie in cookies:
                self.session.cookies.set(cookie["name"], cookie["value"])
        # Send GET request
        response = self.session.get(
            url=os.environ.get("BING_PROXY_URL")
            or "https://edgeservices.bing.com/edgesvc/turing/conversation/create",
        )
        if response.status_code != 200:
            print(f"Status code: {response.status_code}")
            print(response.text)
            print(response.url)
            raise Exception("Authentication failed")
        try:
            self.struct = response.json()
        except (json.decoder.JSONDecodeError, NotAllowedToAccess) as exc:
            raise Exception(
                "Authentication failed. You have not been accepted into the beta.",
            ) from exc
        if self.struct["result"]["value"] == "UnauthorizedRequest":
            raise NotAllowedToAccess(self.struct["result"]["message"])
        if 'X-Sydney-Encryptedconversationsignature' in response.headers:
            self.struct['secAccessToken'] = response.headers['X-Sydney-Encryptedconversationsignature']

    @staticmethod
    async def create(
        proxy: Union[str, None] = None,
        cookies: Union[List[dict], None] = None,
        conversation_id: Union[str, None] = None,
    ) -> "Conversation":
        self = Conversation(async_mode=True)
        self.struct = {
            "conversationId": None,
            "clientId": None,
            "conversationSignature": None,
            "secAccessToken": None,
            "result": {"value": "Success", "message": None},
        }
        self.proxy = proxy
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

        async with AsyncSession(
            headers=HEADERS_INIT_CONVER,
            proxy=proxy,
            impersonate="chrome116",
        ) as s:
            for cookie in cookies:
                s.cookies.set(cookie["name"], cookie["value"])
            url = os.environ.get("BING_PROXY_URL") or "https://www.bing.com/turing/conversation/create"
            if conversation_id:
                url += f"?conversationId={conversation_id}"

            response = await s.get(url=url)
            if response.status_code != 200:
                print(f"Status code: {response.status_code}")
                print(response.text)
                print(response.url)
                raise Exception("Authentication failed")

            try:
                self.struct = response.json()
            except (json.decoder.JSONDecodeError, NotAllowedToAccess) as exc:
                print(response.text)
                raise Exception(
                    "Authentication failed. You have not been accepted into the beta.",
                ) from exc
            if self.struct["result"]["value"] == "UnauthorizedRequest":
                raise NotAllowedToAccess(self.struct["result"]["message"])
            if 'X-Sydney-Encryptedconversationsignature' in response.headers:
                self.struct['secAccessToken'] = response.headers['X-Sydney-Encryptedconversationsignature']

            return self
