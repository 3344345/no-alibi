"""Types accepted by the loopback player API."""

from typing import Annotated
from pydantic import BaseModel, ConfigDict, Field, JsonValue

Identifier = Annotated[
    str, Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9_.:-]+$")
]
Balance = Annotated[
    str, Field(pattern=r"^(?:0\.[0-9]{6}|1\.000000)$", min_length=8, max_length=8)
]


class PlayerInput(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")


class NewCareer(PlayerInput):
    start: Annotated[str, Field(pattern=r"^S0[1-8]$")]
    name: Annotated[str, Field(min_length=1, max_length=32)]
    balance: Balance = "0.500000"
    seed: Annotated[str, Field(min_length=1, max_length=96)] | int | None = None


class PlayerCommand(PlayerInput):
    command_id: Identifier
    expected_revision: Annotated[int, Field(ge=0)]
    kind: Identifier
    confirmation_token: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")] | None = None
    args: dict[str, JsonValue] = Field(default_factory=dict)


class ParseText(PlayerInput):
    text: Annotated[str, Field(min_length=1, max_length=1200)]


class BranchPoint(PlayerInput):
    revision: Annotated[int, Field(ge=0)]
