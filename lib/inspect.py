"""Parse field TSV from the UI bridge. Values of fields are never included."""

from __future__ import annotations


def parse_fields(raw: str) -> list[dict[str, str | bool]]:
    fields: list[dict[str, str | bool]] = []
    for line in raw.splitlines():
        line = line.rstrip("\n")
        if not line or line.startswith("STATUS") or line.startswith("OK"):
            if line.startswith("STATUS"):
                continue
            if line == "OK":
                continue
        parts = line.split("\t")
        if len(parts) < 7:
            continue
        role, subrole, name, description, placeholder, identifier, focused = parts[:7]
        fields.append(
            {
                "role": role,
                "subrole": subrole,
                "name": name,
                "description": description,
                "placeholder": placeholder,
                "identifier": identifier,
                "focused": focused.lower() in {"true", "1", "yes"},
            }
        )
    return fields
