from enum import Enum

try:
    from typing import Literal, Union
except ImportError:
    from typing_extensions import Literal
from typing import Optional

_BASE_OPTION_SETS = [
    # no jailbreak filter
    "nojbf",
    "iyxapbing",
    "iycapbing",
    "dgencontentv3",
    "nointernalsugg",
    "disable_telemetry",
    "machine_affinity",
    "streamf",
    "langdtwb",
    "fdwtlst",
    # "fluxcrplus",
    "fluxprod"
    "eredirecturl",
    # may related to image search
    "gptvnodesc",
    "gptvnoex",
    "sdretrieval",
    "gamaxinvoc",
    "ldsummary",
    "ldqa",
]


class ConversationStyle(Enum):
    creative = _BASE_OPTION_SETS + ["Creative"]
    balanced = _BASE_OPTION_SETS + ["galileo", "gldcl1p"]
    precise = _BASE_OPTION_SETS + ["h3precise"]


CONVERSATION_STYLE_TYPE = Optional[
    Union[ConversationStyle, Literal["creative", "balanced", "precise"]]
]


class Persona(Enum):
    designer = "ai_persona_designer_gpt"
    travel = "flux_vacation_planning_helper_v14"
    cooking = "flux_cooking_helper_v14"
    fitness = "flux_fitness_helper_v14"
    copilot = "fluxcopilot"
    sydney = "fluxsydney"
