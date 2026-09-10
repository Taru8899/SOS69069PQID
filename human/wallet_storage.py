"""Human identity session: stays unlocked until explicit logout (or clear data)."""
from __future__ import annotations
import os
import json

SESSION_FILE = "human_session.json"
_unlocked = False
_cached_identity = None  # in-memory identity dict while unlocked


def _session_path(user_data_dir: str) -> str:
    return os.path.join(user_data_dir, SESSION_FILE)


def set_unlocked(user_data_dir: str, v: bool, identity: dict | None = None) -> None:
    global _unlocked, _cached_identity
    _unlocked = bool(v)
    if v and identity is not None:
        _cached_identity = identity
    if not v:
        _cached_identity = None
    try:
        os.makedirs(user_data_dir, exist_ok=True)
        path = _session_path(user_data_dir)
        if v:
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"unlocked": True}, f)
        else:
            if os.path.isfile(path):
                os.remove(path)
    except Exception:
        pass


def is_unlocked(user_data_dir: str | None = None) -> bool:
    global _unlocked
    if _unlocked:
        return True
    if user_data_dir:
        path = _session_path(user_data_dir)
        if os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if data.get("unlocked"):
                    _unlocked = True
                    return True
            except Exception:
                pass
    return False


def get_cached_identity():
    return _cached_identity


def set_cached_identity(identity: dict | None):
    global _cached_identity
    _cached_identity = identity


def logout_session(user_data_dir: str | None = None):
    global _unlocked, _cached_identity
    _unlocked = False
    _cached_identity = None
    if user_data_dir:
        path = _session_path(user_data_dir)
        try:
            if os.path.isfile(path):
                os.remove(path)
        except Exception:
            pass


def restore_session(user_data_dir: str, load_identity_fn) -> bool:
    """If session flag or identity file exists, restore unlocked + cache identity."""
    global _unlocked, _cached_identity
    idn = load_identity_fn(user_data_dir)
    if not idn:
        logout_session(user_data_dir)
        return False
    # Prefer explicit session file; if missing but identity exists, treat as logged in
    path = _session_path(user_data_dir)
    if os.path.isfile(path) or idn:
        _unlocked = True
        _cached_identity = idn
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"unlocked": True}, f)
        except Exception:
            pass
        return True
    return False
