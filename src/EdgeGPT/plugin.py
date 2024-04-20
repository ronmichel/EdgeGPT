from enum import Enum


class Item:
    def __init__(self, plugin_id: str, option_set: str) -> None:
        self.plugin_id = plugin_id
        self.option_set = option_set


class Plugin(Enum):
    codeInterpreter = Item('', "codeintfile")
    instacart = Item('46664d33-1591-4ce8-b3fb-ba1022b66c11', '0A402EDC')
    kayak = Item('d6be744c-2bd9-432f-95b7-76e103946e34', 'C0BB4EAB')
    klarna = Item('5f143ea3-8c80-4efd-9515-185e83b7cf8a', '606E9E5D')
    openTable = Item('543a7b1b-ebc6-46f4-be76-00c202990a1b', 'E05D72DE')
    search = Item('c310c353-b9f0-4d76-ab0d-1dd5e979cf68', None)
    shop = Item('39e3566a-d481-4d99-82b2-6d739b1e716e', '2E842A93')
    suno = Item('22b7f79d-8ea4-437e-b5fd-3e21f09f7bc1', '014CB21D')
