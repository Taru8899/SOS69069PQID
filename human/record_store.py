from __future__ import annotations
import json, os, shutil, time
from typing import List
from human import storage_prefs as prefs

RECORDS_DIR = "human_records"
ATTEST_DIR = "human_attestations"
IDENTITY_FILE = "human_identity.json"
SESSION_FILE = "human_session.json"
PAGE = 25

def clear_human_data(user_data_dir: str) -> list:
    removed = []
    for name in (IDENTITY_FILE, SESSION_FILE, "human_submit_log.json"):
        path = os.path.join(user_data_dir, name)
        if os.path.isfile(path):
            try:
                os.remove(path)
                removed.append(name)
            except Exception:
                pass
    for dname in (RECORDS_DIR, ATTEST_DIR):
        path = os.path.join(user_data_dir, dname)
        if os.path.isdir(path):
            try:
                shutil.rmtree(path)
                removed.append(dname + "/")
            except Exception:
                pass
    try:
        from human import wallet_storage as hws
        hws.logout_session(user_data_dir)
    except Exception:
        pass
    return removed

def list_records(user_data_dir: str) -> List[dict]:
    path = os.path.join(user_data_dir, RECORDS_DIR)
    if not os.path.isdir(path):
        return []
    out = []
    for fn in os.listdir(path):
        if not fn.endswith(".json"):
            continue
        try:
            with open(os.path.join(path, fn), "r", encoding="utf-8") as f:
                out.append(json.load(f))
        except Exception:
            pass
    out.sort(key=lambda x: x.get("saved_at") or 0, reverse=True)
    return out

def list_records_page(user_data_dir: str, page_index: int = 0):
    items = list_records(user_data_dir)
    total = len(items)
    pages = max(1, (total + PAGE - 1) // PAGE)
    page_index = max(0, min(page_index, pages - 1))
    start = page_index * PAGE
    return items[start:start + PAGE], page_index, pages, total

def save_record(user_data_dir: str, record: dict) -> str:
    path = os.path.join(user_data_dir, RECORDS_DIR)
    os.makedirs(path, exist_ok=True)
    rid = record.get("id") or record.get("hash") or str(int(time.time()))
    record = dict(record)
    record["saved_at"] = int(time.time())
    fp = os.path.join(path, f"{rid}.json")
    with open(fp, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2)
    # enforce cap: delete oldest files beyond max
    rows = list_records(user_data_dir)
    cap = prefs.records_max(user_data_dir)
    for old in rows[cap:]:
        oid = old.get("id")
        if not oid:
            continue
        try:
            os.remove(os.path.join(path, f"{oid}.json"))
        except Exception:
            pass
    return fp

def list_attests(user_data_dir: str) -> list:
    path = os.path.join(user_data_dir, ATTEST_DIR)
    if not os.path.isdir(path):
        return []
    out = []
    for fn in sorted(os.listdir(path), reverse=True):
        try:
            with open(os.path.join(path, fn), "r", encoding="utf-8") as f:
                d = json.load(f)
            d["_file"] = fn
            out.append(d)
        except Exception:
            pass
    return out

def list_attests_page(user_data_dir: str, page_index: int = 0):
    items = list_attests(user_data_dir)
    total = len(items)
    pages = max(1, (total + PAGE - 1) // PAGE)
    page_index = max(0, min(page_index, pages - 1))
    start = page_index * PAGE
    return items[start:start + PAGE], page_index, pages, total

def trim_attests(user_data_dir: str):
    path = os.path.join(user_data_dir, ATTEST_DIR)
    if not os.path.isdir(path):
        return
    files = sorted(os.listdir(path), reverse=True)
    cap = prefs.attest_max(user_data_dir)
    for fn in files[cap:]:
        try:
            os.remove(os.path.join(path, fn))
        except Exception:
            pass
