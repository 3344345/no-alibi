"""Strict fields permitted to cross the player's HTTP boundary."""

from typing import Annotated, Literal
from pydantic import Field
from .player_api import Balance, PlayerInput

NonNegative = Annotated[int, Field(ge=0)]
Unit = Annotated[float, Field(ge=0, le=1)]
Digest = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
Value = str | int | float | bool


class Named(PlayerInput):
    id: str
    name: str
    description: str


class Person(Named):
    role: str
    present: bool
    origin: str | None = None


class Place(Named):
    accessible: bool
    access: str


class Project(Named):
    status: str
    report: str
    request: NonNegative
    groups: NonNegative
    owner: str
    public_use: bool
    passage: str | None
    maintenance: bool


class Player(PlayerInput):
    name: str
    role: str
    start: str
    location_id: str
    location: str
    age: NonNegative
    position: str
    quarter: NonNegative
    fatigue: int
    pressure: int
    resilience: int
    duties: str


class Document(Named):
    description: str = ""
    title: str
    source: str
    source_id: str
    date: str
    received_minute: NonNegative
    receipt_order: NonNegative
    scope: str
    body: str
    version: str
    kind: str
    refs: list[str]


class Transition(PlayerInput):
    minute: NonNegative
    ref: str
    status: str
    text: str


class Case(Named):
    title: str
    status: str
    detail: str
    history: list[Transition]
    pending_review: str | None = None
    reviewed_docs: list[str] = Field(default_factory=list)


class CalendarItem(PlayerInput):
    id: str
    due: NonNegative
    title: str


class Commitment(CalendarItem):
    creditor: str
    status: str
    type: str
    ref: str
    version: NonNegative


class Job(CalendarItem):
    kind: str
    visible: bool


class Finances(PlayerInput):
    annual_remaining: NonNegative
    quarter_remaining: NonNegative
    reserved: NonNegative
    paid: NonNegative
    groups_available: NonNegative
    savings: NonNegative


class Note(PlayerInput):
    text: str
    kind: str
    minute: NonNegative
    ref: str
    source_doc: str | None = None


class Notebook(PlayerInput):
    accessible: bool
    location: str
    entries: list[Note]


class Ending(Named):
    title: str
    minute: NonNegative
    refs: list[str]
    resume_policy: str


class Report(PlayerInput):
    id: str
    title: str
    body: str
    refs: list[str]


class Arc(PlayerInput):
    id: str
    title: str
    status: str


class Terms(PlayerInput):
    amount: NonNegative
    groups: NonNegative


class Offer(PlayerInput):
    id: str
    name: str
    version: NonNegative
    description: str
    terms: dict[str, Terms]
    status: str
    ref: str | None = None
    deadline: NonNegative | None = None


class Family(PlayerInput):
    training: str
    care: str


class Choice(PlayerInput):
    label: str
    value: Value


class ActionField(PlayerInput):
    name: str
    label: str
    type: Literal["select", "text", "textarea", "number", "checkbox"]
    default: Value | None = None
    required: bool = False
    maxLength: NonNegative | None = None
    options: list[Choice] = Field(default_factory=list)


class Action(PlayerInput):
    kind: str
    label: str
    description: str
    cost: str
    category: str
    enabled: bool
    reason: str
    args: dict[str, Value]
    fields: list[ActionField]
    confirm: str | bool = False
    confirmation_token: Digest | None = None


class Receipt(PlayerInput):
    id: str
    status: Literal["accepted", "unavailable", "blocked"]
    text: str


class Entry(PlayerInput):
    id: str
    minute: NonNegative
    kind: str
    title: str
    text: str
    actor: str
    refs: list[str]


class Change(PlayerInput):
    target: Balance
    start: Unit
    minute: NonNegative
    version: NonNegative


class Policy(PlayerInput):
    target: Balance
    effective: Unit
    version: NonNegative
    parameter_package_hash: Digest
    transition_end: NonNegative
    trajectory: list[Change]


class Parent(PlayerInput):
    world_id: str
    revision: NonNegative


class DispatchPlan(PlayerInput):
    key: str
    route: Literal["bridge", "baths"]
    label: str
    leave: str
    bath_at: str | None
    arrive: str
    nurses: NonNegative
    transfer: bool
    marked: bool


class NightBus(PlayerInput):
    stage: Literal["invitation", "waiting", "playing", "ending"]
    act: str
    title: str
    place: str
    body: str
    reply: str
    due: NonNegative | None
    art: Literal["nightbus", "depot"]
    dispatch: list[DispatchPlan] = Field(default_factory=list)


class PlayerView(PlayerInput):
    night_bus: NightBus | None = None
    id: str
    world_id: str
    player_id: Literal["player"]
    world_revision: NonNegative
    visible_event_sequence: NonNegative
    observation_watermark: str
    scene_id: str
    name: str
    start: str
    revision: NonNegative
    minute: NonNegative
    quarter: NonNegative
    player: Player
    opening: str
    location: Named
    locations: list[Place]
    people: list[Person]
    cases: list[Case]
    projects: list[Project]
    documents: list[Document]
    commitments: list[Commitment]
    finances: Finances
    notebook: Notebook
    ending: Ending | None
    reports: list[Report]
    arcs: list[Arc]
    offers: list[Offer]
    actions: list[Action]
    family: Family
    busy: Job | None
    last_action_results: list[Receipt]
    timeline: list[Entry]
    policy: Policy
    parent: Parent | None
    appointments: list[CalendarItem]
    view_hash: Digest
