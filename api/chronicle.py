"""Chronicle endpoints protected by the same local session as the county career."""

from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from game.chronicle import Branch, Campaign, ChronicleStore, Command, NewChronicle


def chronicle_router(store: ChronicleStore):
    router = APIRouter(prefix="/api/chronicle")

    @router.get("")
    def index(campaign: Campaign = "family"):
        return store.catalogue(campaign)

    @router.post("", status_code=201)
    def create(body: NewChronicle):
        return store.create(body.name, body.campaign, body.start_chapter, body.opening_choice, body.edition)

    @router.post("/import")
    def restore(body: dict[str, Any]):
        return store.restore(body)

    @router.get("/{career_id}")
    def view(career_id: str):
        return store.view(career_id)

    @router.post("/{career_id}/choices")
    def choose(career_id: str, body: Command):
        return store.choose(career_id, body)

    @router.post("/{career_id}/fork", status_code=201)
    def fork(career_id: str, branch: Branch):
        return store.fork(career_id, branch)

    @router.get("/{career_id}/export")
    def export(career_id: str):
        return JSONResponse(
            store.export(career_id),
            headers={
                "Content-Disposition": 'attachment; filename="juzhongshi-chronicle.json"'
            },
        )

    return router
