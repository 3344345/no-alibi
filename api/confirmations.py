"""Bind major decisions to the exact terms and world revision shown in this session."""

import hashlib
import hmac
import secrets
from game.balance import canonical


def consequence(kind, args):
    if kind == "present_item":
        return "确认后将记录此次尝试，在场者可能注意到你的举动。"
    if kind == "career_exit":
        return "提交后将启动本次申请的岗位交接。"
    if kind == "stage_end":
        return "确认后将结束本段生涯。"
    if kind == "confirm_note" and args.get("choice") == "yes":
        return "销毁后，本份原件将无法再读取。"
    if kind == "finding":
        return "提交后，这份程序意见会作为正式记录送达。"
    return None


class Confirmations:
    def __init__(self):
        self._key = secrets.token_bytes(32)

    def signature(self, world_id, rev, kind, args):
        payload = canonical(["player", world_id, rev, kind, args]).encode()
        return hmac.new(self._key, payload, hashlib.sha256).hexdigest()

    def attach(self, original):
        view = {**original, "id": original["world_id"]}
        if "actions" not in view:
            return view
        actions = []
        for item in view["actions"]:
            reason = consequence(item["kind"], item.get("args", {}))
            if reason:
                item = {
                    **item,
                    "confirm": reason,
                    "confirmation_token": self.signature(
                        view["id"], view["revision"], item["kind"], item.get("args", {})
                    ),
                }
            actions.append(item)
        return {**view, "actions": actions}

    def accepts(self, world_id, command):
        if not consequence(command.kind, command.args):
            return True
        return hmac.compare_digest(
            self.signature(
                world_id, command.expected_revision, command.kind, command.args
            ),
            command.confirmation_token or "",
        )
