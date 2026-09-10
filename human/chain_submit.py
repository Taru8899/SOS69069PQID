"""
Optional on-chain submit: one recordSignature to SOS contract.
Marks PQID via payloadHash + metadata; EIP-712 per contract.
"""
from __future__ import annotations
from pure_crypto import keccak256
from sos_core import sign_record, CONTRACT_ADDRESS, address_from_private_key
import tx as txmod

CHAIN_ID = 1
CONTRACT = CONTRACT_ADDRESS  # 0x7373DBC24Dcd785896E8Ac3d5372c6ced9B75a8A

def pqid_payload_hash(fingerprint: str, kind: str, local_hash: str) -> str:
    raw = f"SOS69069-PQID|1|{kind}|{fingerprint}|{local_hash}".encode()
    return "0x" + keccak256(raw).hex()

def pqid_metadata(kind: str, fingerprint: str, local_hash: str) -> str:
    """<=64 chars. Mark PQID traffic on-chain."""
    fp = (fingerprint or "").replace("-", "")[:8]
    h = (local_hash or "").replace("0x", "")[:12]
    k = (kind or "x")[:8]
    meta = f"PQID|1|{k}|{fp}|{h}"
    return meta[:64]

def describe_submit_bridge() -> str:
    return (
        "Optional: one recordSignature to SOS contract "
        f"{CONTRACT}.\n"
        "EIP-712 binds signer, intendedTo, payloadHash, metadata.\n"
        "Push += signer, Trust += intendedTo, Effective = Trust - Push."
    )

def try_get_main_payer_key():
    try:
        from kivy.app import App
        app = App.get_running_app()
        if hasattr(app, "get_payer_key"):
            k = app.get_payer_key()
            if k:
                return k
        return getattr(app, "private_key", None)
    except Exception:
        return None

def try_get_main_payer_address():
    k = try_get_main_payer_key()
    if not k:
        return None
    try:
        return address_from_private_key(k)
    except Exception:
        return None

def submit_record_signature(
    eth_privkey_hex: str,
    intended_to: str,
    payload_hash: str,
    metadata: str,
    signer: str | None = None,
) -> dict:
    """Sign EIP-712 with eth key and broadcast recordSignature."""
    signed = sign_record(
        eth_privkey_hex, CHAIN_ID, intended_to, payload_hash, metadata, CONTRACT
    )
    result = txmod.send_record_signature(
        eth_privkey_hex,
        intended_to,
        payload_hash,
        signed["signature"],
        metadata,
        signer=signed["signer"],
    )
    result["metadata"] = metadata
    result["payloadHash"] = payload_hash
    result["signer"] = signed["signer"]
    result["intendedTo"] = intended_to
    return result

def optional_submit(
    user_data_dir: str,
    kind: str,
    fingerprint: str,
    local_hash: str,
    eth_privkey_hex: str | None = None,
    intended_to: str | None = None,
) -> dict:
    """
    Full optional path: mark + sign + send + local log.
    eth_privkey defaults to connected main payer if any.
    intended_to defaults to signer (self) for presence-style +1 push+trust.
    """
    from human import submit_log as slog

    key = eth_privkey_hex or try_get_main_payer_key()
    if not key:
        entry = {
            "kind": kind,
            "fingerprint": fingerprint,
            "local_hash": local_hash,
            "status": "intended",
            "error": "no eth wallet connected",
        }
        slog.add(user_data_dir, entry)
        return entry

    payload = pqid_payload_hash(fingerprint, kind, local_hash or "")
    meta = pqid_metadata(kind, fingerprint, local_hash or payload)
    signer = address_from_private_key(key)
    ito = intended_to or signer
    try:
        result = submit_record_signature(key, ito, payload, meta, signer=signer)
        entry = {
            "kind": kind,
            "fingerprint": fingerprint,
            "local_hash": local_hash,
            "payload_hash": payload,
            "metadata": meta,
            "signer": result.get("signer") or signer,
            "intendedTo": ito,
            "tx_hash": result.get("txHash"),
            "status": "submitted",
        }
        slog.add(user_data_dir, entry)
        return entry
    except Exception as e:
        entry = {
            "kind": kind,
            "fingerprint": fingerprint,
            "local_hash": local_hash,
            "payload_hash": payload,
            "metadata": meta,
            "status": "failed",
            "error": str(e),
        }
        slog.add(user_data_dir, entry)
        return entry
