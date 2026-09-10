"""User-selectable local caps; null = main-SOS-aligned defaults."""
from __future__ import annotations
import json, os

PREFS_FILE = "human_storage_prefs.json"

# Align with main local_store order of magnitude
DEFAULT_RECORDS_MAX = 500      # CAP_PRES-like
DEFAULT_ATTEST_MAX = 500
DEFAULT_SUBMIT_LOG_MAX = 200

def _path(user_data_dir: str) -> str:
    return os.path.join(user_data_dir, PREFS_FILE)

def load_prefs(user_data_dir: str) -> dict:
    path = _path(user_data_dir)
    if not os.path.isfile(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f) or {}
    except Exception:
        return {}

def save_prefs(user_data_dir: str, prefs: dict) -> None:
    os.makedirs(user_data_dir, exist_ok=True)
    path = _path(user_data_dir)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(prefs, f, indent=2)
    os.replace(tmp, path)

def _cap(prefs: dict, key: str, default: int) -> int:
    v = prefs.get(key)
    if v is None or v == "" or v == 0:
        return default
    try:
        n = int(v)
        return n if n > 0 else default
    except Exception:
        return default

def records_max(user_data_dir: str) -> int:
    return _cap(load_prefs(user_data_dir), "records_max", DEFAULT_RECORDS_MAX)

def attest_max(user_data_dir: str) -> int:
    return _cap(load_prefs(user_data_dir), "attest_max", DEFAULT_ATTEST_MAX)

def submit_log_max(user_data_dir: str) -> int:
    return _cap(load_prefs(user_data_dir), "submit_log_max", DEFAULT_SUBMIT_LOG_MAX)
