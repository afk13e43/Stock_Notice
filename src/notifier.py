"""Discord webhook notifier."""
from __future__ import annotations

import os
import sys

import requests


def get_webhook_url() -> str | None:
    return os.environ.get("DISCORD_WEBHOOK_URL")


def send(messages: list[str]) -> None:
    """Send a bundled Discord notification. No-op if there are no messages."""
    if not messages:
        return

    url = get_webhook_url()
    if not url:
        print("[notifier] DISCORD_WEBHOOK_URL not set — printing instead:", file=sys.stderr)
        for m in messages:
            print(m, file=sys.stderr)
        return

    content = "\n\n".join(messages)
    # Discord content cap is 2000 chars; chunk if needed.
    for chunk in _chunk(content, 1900):
        resp = requests.post(url, json={"content": chunk}, timeout=15)
        resp.raise_for_status()


def _chunk(text: str, size: int) -> list[str]:
    if len(text) <= size:
        return [text]
    parts: list[str] = []
    remaining = text
    while len(remaining) > size:
        cut = remaining.rfind("\n", 0, size)
        if cut == -1:
            cut = size
        parts.append(remaining[:cut])
        remaining = remaining[cut:].lstrip("\n")
    if remaining:
        parts.append(remaining)
    return parts
