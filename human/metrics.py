"""
Wallet metrics for connected eth address.

On-chain (SOS contract): pushCountOf / trustCountOf / effectiveOf
  Push  = times address was signer
  Trust = times address was intendedTo
  Effective = Trust - Push

PQID-only local: submit log rows status=submitted, same signer/intendedTo rules.

PQID-only chain cross-check: SignatureRecorded logs where metadata starts with
  "PQID|" and signer/intendedTo match connected address.
"""
from __future__ import annotations

from typing import Optional


def _norm(addr: str | None) -> str:
    if not addr:
        return ""
    a = addr.strip().lower()
    if not a.startswith("0x"):
        a = "0x" + a
    return a


def stats_onchain(address: str) -> dict:
    """Full SOS ledger stats for address via contract view."""
    import rpc
    s = rpc.stats_of(address)
    return {
        "push": int(s.get("push") or 0),
        "trust": int(s.get("trust") or 0),
        "effective": int(s.get("effective") or 0),
        "source": "contract",
    }


def stats_pqid_local(user_data_dir: str, address: str) -> dict:
    """Count local submitted log by signer / intendedTo."""
    from human import submit_log as slog
    addr = _norm(address)
    push = trust = 0
    for e in slog.load_all(user_data_dir):
        if e.get("status") != "submitted":
            continue
        if _norm(e.get("signer")) == addr:
            push += 1
        if _norm(e.get("intendedTo")) == addr:
            trust += 1
    return {
        "push": push,
        "trust": trust,
        "effective": trust - push,
        "source": "local_log",
    }


def stats_pqid_chain(address: str, max_per_direction: int = 200) -> dict:
    """
    Cross-check: fetch SignatureRecorded for address as signer (push) and as
    intendedTo (trust); keep only metadata starting with PQID|.
    """
    import rpc
    addr = _norm(address)
    push = trust = 0
    seen_push = set()
    seen_trust = set()

    try:
        as_signer = rpc.fetch_messages(address, direction="push", max_results=max_per_direction)
    except Exception:
        as_signer = []
    try:
        as_intended = rpc.fetch_messages(address, direction="trust", max_results=max_per_direction)
    except Exception:
        as_intended = []

    for ev in as_signer:
        meta = (ev.get("metadata") or "").strip()
        if not meta.startswith("PQID|"):
            continue
        if _norm(ev.get("signer")) != addr:
            continue
        key = (ev.get("txHash"), ev.get("logIndex"))
        if key in seen_push:
            continue
        seen_push.add(key)
        push += 1

    for ev in as_intended:
        meta = (ev.get("metadata") or "").strip()
        if not meta.startswith("PQID|"):
            continue
        if _norm(ev.get("intendedTo")) != addr:
            continue
        key = (ev.get("txHash"), ev.get("logIndex"))
        if key in seen_trust:
            continue
        seen_trust.add(key)
        trust += 1

    return {
        "push": push,
        "trust": trust,
        "effective": trust - push,
        "source": "chain_logs_pqid",
    }


def format_block(title: str, s: dict) -> str:
    return (
        f"{title}\n"
        f"  Push: {s.get('push', 0)}   "
        f"Trust: {s.get('trust', 0)}   "
        f"Effective: {s.get('effective', 0)}"
    )
