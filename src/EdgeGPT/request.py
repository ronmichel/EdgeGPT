import uuid
from datetime import datetime
from typing import Union

from .plugin import Item
from .conversation_style import CONVERSATION_STYLE_TYPE
from .conversation_style import ConversationStyle, Persona
from .plugin import Plugin
from .utilities import get_location_hint_from_locale
from .utilities import get_ran_hex
from .utilities import guess_locale


class ChatHubRequest:
    def __init__(
            self,
            conversation_signature: str,
            client_id: str,
            conversation_id: str,
            invocation_id: int = 3,
    ) -> None:
        self.struct: dict = {}

        self.client_id: str = client_id
        self.conversation_id: str = conversation_id
        self.conversation_signature: str = conversation_signature
        self.invocation_id: int = invocation_id

    def update(
            self,
            prompt: str,
            conversation_style: CONVERSATION_STYLE_TYPE,
            webpage_context: Union[str, None] = None,
            locale: str = guess_locale(),
            no_search: bool = True,
            persona: Persona = Persona.copilot,
            plugins: set[Plugin] = {},
            image_url: str = None,
    ) -> None:
        options = [
            "deepleo",
            "enable_debug_commands",
            "disable_emoji_spoken_text",
            "enablemm",
        ]
        if conversation_style:
            if not isinstance(conversation_style, ConversationStyle):
                conversation_style = getattr(ConversationStyle, conversation_style)
            options = conversation_style.value.copy()

        plugin_params = []
        is_search_needed_for_plugin = False
        for plugin in plugins:
            val: Item = plugin.value
            if val.id is not None:
                plugin_params.append({
                    "id": val.plugin_id,
                    "category": 1
                })

            if val.option_set is not None:
                options.append(val.option_set)

            if (not is_search_needed_for_plugin) and plugin != Plugin.codeInterpreter:
                is_search_needed_for_plugin = True

        if is_search_needed_for_plugin and (Plugin.search not in plugins):
            plugin_params.append({
                "id": Plugin.search.value.id,
                "category": 1
            })

        if (not is_search_needed_for_plugin) and no_search:
            options.append('nosearchall')

        options.append(persona.value)

        message_id = str(uuid.uuid4())
        # Get the current local time
        now_local = datetime.now()

        # Get the current UTC time
        now_utc = datetime.utcnow()

        # Calculate the time difference between local and UTC time
        timezone_offset = now_local - now_utc

        # Get the offset in hours and minutes
        offset_hours = int(timezone_offset.total_seconds() // 3600)
        offset_minutes = int((timezone_offset.total_seconds() % 3600) // 60)

        # Format the offset as a string
        offset_string = f"{offset_hours:+03d}:{offset_minutes:02d}"

        # Get current time
        timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S") + offset_string
        message = {
            "locale": locale,
            "market": locale,
            "region": locale[-2:],  # en-US -> US
            "locationHints": get_location_hint_from_locale(locale),
            "timestamp": timestamp,
            "author": "user",
            "inputMethod": "Keyboard",
            "text": prompt,
            "messageType": "Chat",
            "messageId": message_id,
            "requestId": message_id,
        }
        if image_url is not None:
            message["imageUrl"] = image_url

        self.struct = {
            "arguments": [
                {
                    "source": "cib",
                    "optionsSets": options,
                    "allowedMessageTypes": [
                        "ActionRequest",
                        "Chat",
                        "Context",
                        "InternalSearchQuery",
                        "InternalSearchResult",
                        "Disengaged",
                        "InternalLoaderMessage",
                        "Progress",
                        "RenderCardRequest",
                        "AdsQuery",
                        "SemanticSerp",
                        "GenerateContentQuery",
                        "SearchQuery",
                    ],
                    "sliceIds": [
                        "0311tccs0",
                        "gldidentitycf",
                        "qnav2table1",
                        "fltlatest",
                        "ntbkwco",
                        "cntralign2",
                        "cntralign",
                        "bcece403t",
                        "crtcachenock",
                        "romiccf",
                        "rwt2",
                        "cleanjsonctrl",
                        "advtoknmic",
                        "cacblvsdscf",
                        "408mems0",
                        "shopgptctrl",
                        "0329mupcsts0",
                        "unionfdbk",
                        "fpallsticy",
                        "0404redhoo",
                        "saisgrds0",
                        "duptelfix",
                        "fixertel",
                        "ntbkgoldcf",
                        "kcclickthrucf",
                        "cacfrwebt2",
                        "sswebtop1cf",
                        "sswebtop2",
                        "sstopcf"
                    ],
                    "verbosity": "verbose",
                    "scenario": "SERP",
                    "plugins": plugin_params,
                    "traceId": get_ran_hex(32),
                    "gptId": persona.name,
                    "isStartOfSession": self.invocation_id == 3,
                    "message": message,
                    "tone": conversation_style.name.capitalize(),  # Make first letter uppercase
                    "requestId": message_id,
                    "conversationSignature": self.conversation_signature,
                    "participant": {
                        "id": self.client_id,
                    },
                    "conversationId": self.conversation_id,
                },
            ],
            "invocationId": str(self.invocation_id),
            "target": "chat",
            "type": 4,
        }

        if webpage_context:
            self.struct["arguments"][0]["previousMessages"] = [
                {
                    "author": "user",
                    "description": webpage_context,
                    "contextType": "WebPage",
                    "messageType": "Context",
                    "messageId": "discover-web--page-ping-mriduna-----",
                },
            ]
        self.invocation_id += 1
        # print(json.dumps(self.struct, indent=2, ensure_ascii=False))
