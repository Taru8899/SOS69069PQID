"""Local log of PQID on-chain submits (intended/submitted)."""
from __future__ import annotations
import json, os, time
from human import storage_prefs as prefs

LOG_FILE = "human_submit_log.json"
PAGE = 25

def _path(user_data_dir: str) -> str:
    return os.path.join(user_data_dir, LOG_FILE)

def load_all(user_data_dir: str) -> list:
    path = _path(user_data_dir)
    if not os.path.isfile(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        items = data.get("items") or []
        return items if isinstance(items, list) else []
    except Exception:
        return []

def _write(user_data_dir: str, items: list) -> None:
    os.makedirs(user_data_dir, exist_ok=True)
    cap = prefs.submit_log_max(user_data_dir)
    items = sorted(items, key=lambda x: x.get("ts") or 0, reverse=True)[:cap]
    path = _path(user_data_dir)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"updated_at": int(time.time()), "items": items}, f, indent=2)
    os.replace(tmp, path)

def add(user_data_dir: str, entry: dict) -> dict:
    items = load_all(user_data_dir)
    entry = dict(entry)
    entry.setdefault("ts", int(time.time()))
    items.insert(0, entry)
    _write(user_data_dir, items)
    return entry

def page(user_data_dir: str, page_index: int = 0) -> tuple:
    items = load_all(user_data_dir)
    total = len(items)
    pages = max(1, (total + PAGE - 1) // PAGE)
    page_index = max(0, min(page_index, pages - 1))
    start = page_index * PAGE
    return items[start:start + PAGE], page_index, pages, total

def local_kind_counts(user_data_dir: str) -> dict:
    """Product-side counts by kind (submitted only)."""
    trust_kinds = {"identity", "verify", "attest"}
    push_kinds = {"record", "chain"}
    trust = push = effective = 0
    for e in load_all(user_data_dir):
        if e.get("status") != "submitted":
            continue
        k = e.get("kind") or ""
        if k in trust_kinds:
            trust += 1
        if k in push_kinds:
            push += 1
        effective += 1
    return {"trust": trust, "push": push, "effective": effective}
