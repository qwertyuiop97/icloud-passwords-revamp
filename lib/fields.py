"""Classify login fields. Password text is never read or returned."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

USERNAME_HINTS = (
    "user",
    "email",
    "e-mail",
    "login",
    "account",
    "identifier",
    "username",
    "userid",
    "user name",
    "netid",
    "net id",
    "net-id",
    "phone",
    "apple id",
    "handle",
)
PASSWORD_HINTS = ("password", "passwd", "passcode", "pass phrase", "passphrase", "secret")
OTP_HINTS = (
    "otp",
    "totp",
    "verification code",
    "one-time",
    "one time",
    "2fa",
    "mfa",
    "authenticator",
)
SECURE_SUBROLES = {"AXSecureTextField"}
TEXT_ROLES = {"AXTextField", "AXComboBox", "AXTextArea", "AXStaticText"}


def _blob(field: dict[str, Any]) -> str:
    parts = [
        field.get("name") or "",
        field.get("title") or "",
        field.get("description") or "",
        field.get("placeholder") or "",
        field.get("identifier") or "",
        field.get("help") or "",
        field.get("label") or "",
        field.get("role_description") or "",
    ]
    return " ".join(parts).lower()


def is_secure(field: dict[str, Any]) -> bool:
    sub = (field.get("subrole") or "")
    role = (field.get("role") or "")
    return sub in SECURE_SUBROLES or role == "AXSecureTextField"


def is_otp_field(field: dict[str, Any]) -> bool:
    if is_secure(field):
        return False
    blob = _blob(field)
    return any(hint in blob for hint in OTP_HINTS)


def is_password_field(field: dict[str, Any]) -> bool:
    if is_secure(field):
        return True
    blob = _blob(field)
    if any(hint in blob for hint in USERNAME_HINTS):
        return False
    return any(hint in blob for hint in PASSWORD_HINTS)


def is_username_field(field: dict[str, Any]) -> bool:
    if is_secure(field) or is_password_field(field) or is_otp_field(field):
        return False
    blob = _blob(field)
    if any(hint in blob for hint in PASSWORD_HINTS):
        return False
    if any(hint in blob for hint in USERNAME_HINTS):
        return True
    role = field.get("role") or ""
    return role in {"AXTextField", "AXComboBox"}


def may_receive_password(field: dict[str, Any] | None) -> bool:
    """Password may only go into a secure field, never a username field."""
    if not field:
        return False
    if is_username_field(field):
        return False
    if any(hint in _blob(field) for hint in USERNAME_HINTS) and not is_secure(field):
        return False
    return is_password_field(field)


def may_receive_username(field: dict[str, Any] | None) -> bool:
    if not field:
        return False
    if is_secure(field) or is_password_field(field):
        return False
    return is_username_field(field) or (field.get("role") in {"AXTextField", "AXComboBox"})


@dataclass(frozen=True)
class FillPlan:
    mode: str  # both | username | password | none
    username_field: dict[str, Any] | None
    password_field: dict[str, Any] | None

    def validate(self) -> None:
        if self.password_field is not None and not may_receive_password(self.password_field):
            raise ValueError("refusing to send a password to a non-password field")
        if self.username_field is not None and is_secure(self.username_field):
            raise ValueError("refusing to treat a secure field as username")
        if self.username_field is not None and self.password_field is not None:
            if self.username_field is self.password_field:
                raise ValueError("username and password cannot be the same field")


def _pick(candidates: list[dict[str, Any]], focused: dict[str, Any] | None) -> dict[str, Any]:
    if focused in candidates:
        return focused
    focused_list = [f for f in candidates if f.get("focused")]
    if focused_list:
        return focused_list[0]
    return candidates[0]


def plan_fill(fields: list[dict[str, Any]]) -> FillPlan:
    """Decide what to paste.

    - Login form with username + password fields: fill both.
    - Only a password field (or focus in a password field with no username): password only.
    - Only a username field: username only.
    - Never put a password into a username field.
    """
    users = [f for f in fields if is_username_field(f)]
    passwords = [f for f in fields if is_password_field(f)]
    focused = next((f for f in fields if f.get("focused")), None)

    if users and passwords:
        plan = FillPlan("both", _pick(users, focused), _pick(passwords, focused))
    elif focused and is_password_field(focused) and may_receive_password(focused):
        plan = FillPlan("password", None, focused)
    elif focused and may_receive_username(focused) and not passwords:
        plan = FillPlan("username", focused, None)
    elif passwords and not users:
        plan = FillPlan("password", None, _pick(passwords, focused))
    elif users and not passwords:
        plan = FillPlan("username", _pick(users, focused), None)
    else:
        plan = FillPlan("none", None, None)
    plan.validate()
    return plan
