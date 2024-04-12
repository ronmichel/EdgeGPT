import json
import locale
import random
import sys
from typing import Union

from .constants import DELIMITER
from .locale import LocationHint


def append_identifier(msg: dict) -> str:
    # Convert dict to json string
    return json.dumps(msg, ensure_ascii=False) + DELIMITER


def get_ran_hex(length: int = 32) -> str:
    return "".join(random.choice("0123456789abcdef") for _ in range(length))


def get_location_hint_from_locale(locale: str) -> Union[dict, None]:
    locale = locale.lower()
    if locale == "en-gb":
        hint = LocationHint.UK.value
    elif locale == "en-ie":
        hint = LocationHint.EU.value
    elif locale == "zh-cn":
        hint = LocationHint.CHINA.value
    elif locale == "zh-hk":
        hint = LocationHint.HONGKONG.value
    elif locale == "zh-tw":
        hint = LocationHint.TW.value
    else:
        hint = LocationHint.USA.value
    return hint.get("LocationHint")


def guess_locale() -> str:
    if sys.platform.startswith("win"):
        return "en-us"
    loc, _ = locale.getlocale()
    return loc.replace("_", "-") if loc else "en-us"


def parse_search_result(message):
    if 'Web search returned no relevant result' in message['hiddenText']:
        return [{
            'title': 'No relevant result',
            'url': None,
            'snippet': message['hiddenText']
        }]

    data = []
    for group in json.loads(message['text']).values():
        for item in group:
            data.append({
                'title': item['title'],
                'url': item['url'],
            })

    return data
