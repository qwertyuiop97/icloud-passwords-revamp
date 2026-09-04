"""Turn a selected login + form fields into copy/paste steps."""

from __future__ import annotations

import json
from typing import Any

from .fields import FillPlan, may_receive_password, may_receive_username, plan_fill


ALLOWED_ACTIONS = {
    "fill",
    "copy_password",
    "copy_username",
    "copy_otp",
    "reveal",
}


def parse_account(arg: str) -> dict[str, str]:
    data = json.loads(arg)
    if not isinstance(data, dict):
        raise ValueError("account payload must be an object")
    title = str(data.get("title") or "").strip()
    username = str(data.get("username") or "").strip()
    if not title:
        raise ValueError("account payload missing title")
    if "password" in data or "otp" in data or "secret" in data:
        raise ValueError("account payload must not include secrets")
    return {"title": title, "username": username}


def steps_for(
    action: str,
    fields: list[dict[str, Any]],
    fill_both: bool = True,
) -> list[dict[str, str]]:
    """Copy/paste steps. `paste` is username, password, or none."""
    if action not in ALLOWED_ACTIONS:
        raise ValueError(f"unknown action {action}")
    if action == "reveal":
        return [{"menu": "none", "paste": "none", "select": "account"}]
    if action == "copy_username":
        return [{"menu": "username", "paste": "none"}]
    if action == "copy_password":
        return [{"menu": "password", "paste": "none", "conceal": "yes"}]
    if action == "copy_otp":
        return [{"menu": "otp", "paste": "none"}]

    if action == "fill" and not fill_both:
        focused = next((f for f in fields if f.get("focused")), None)
        if focused and may_receive_password(focused):
            return [{"menu": "password", "paste": "password", "conceal": "yes", "clear": "yes"}]
        if focused and may_receive_username(focused):
            return [{"menu": "username", "paste": "username"}]

    plan: FillPlan = plan_fill(fields)
    steps: list[dict[str, str]] = []
    if plan.mode in {"both", "username"} and plan.username_field is not None:
        if not may_receive_username(plan.username_field):
            raise ValueError("username target failed safety check")
        steps.append({"menu": "username", "paste": "username"})
    if plan.mode in {"both", "password"} and plan.password_field is not None:
        if not may_receive_password(plan.password_field):
            raise ValueError("password target failed safety check")
        steps.append({"menu": "password", "paste": "password", "conceal": "yes", "clear": "yes"})
    if not steps:
        # No form fields: copy the user name, never dump a password blindly.
        steps.append({"menu": "username", "paste": "none"})
    return steps
