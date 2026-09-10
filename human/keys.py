"""
Optional gas-payer wallet ("connect wallet").

This is separate from the human identity key (human/identity.py). It is the
Ethereum wallet a user may optionally connect so the app can sign the
EIP-712 Record and broadcast `recordSignature` to the SOS69069 contract on
their behalf. Nothing here ever runs unless the user explicitly imports or
generates a wallet on the WALLET screen, and it is only ever used when the
user taps an "optional submit" button.

Storage:
- The private key never leaves the device and is never sent anywhere except
  as a locally-signed raw transaction broadcast to a public RPC endpoint.
- If the user sets a passphrase, the key is encrypted at rest with a simple
  keccak256-keystream stream cipher (this app is pure-Python / zero
  C-extensions, so no AES lib is available). Without a passphrase the key is
  stored the same way the existing human identity key already is (plain
  JSON in the app's private data dir).
- Once unlocked for the running session, the decrypted key is cached in
  memory only (never re-written to disk) until disconnect/logout.
"""
from __future__ import annotations
import os
import json
import secrets
from typing import Optional

from pure_crypto import keccak256
from sos_core import address_from_private_key

WALLET_FILE = "eth_wallet.json"
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141

_cached_key: Optional[str] = None  # decrypted hex private key, memory-only


def _path(user_data_dir: str) -> str:
    return os.path.join(user_data_dir, WALLET_FILE)


def is_valid_private_key(hex_str: str) -> bool:
    try:
        h = (hex_str or "").strip().replace("0x", "").replace("0X", "")
        if len(h) != 64:
            return False
        v = int(h, 16)
        return 0 < v < N
    except Exception:
        return False


def _normalize(hex_str: str) -> str:
    h = hex_str.strip().replace("0x", "").replace("0X", "")
    return "0x" + h.lower()


def generate_private_key() -> str:
    sk_int = secrets.randbits(256) % N or 1
    return "0x" + hex(sk_int)[2:].zfill(64)


def _keystream(salt: bytes, passphrase: str, nbytes: int) -> bytes:
    out = b""
    counter = 0
    pw = passphrase.encode("utf-8")
    while len(out) < nbytes:
        out += keccak256(salt + pw + counter.to_bytes(4, "big"))
        counter += 1
    return out[:nbytes]


def _xor(a: bytes, b: bytes) -> bytes:
    return bytes(x ^ y for x, y in zip(a, b))


def has_wallet(user_data_dir: str) -> bool:
    return os.path.isfile(_path(user_data_dir))


def get_wallet_meta(user_data_dir: str) -> Optional[dict]:
    """Non-secret info only: address + whether it's passphrase-protected."""
    p = _path(user_data_dir)
    if not os.path.isfile(p):
        return None
    try:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {
            "address": data.get("address"),
            "encrypted": bool(data.get("encrypted")),
            "created": data.get("created"),
        }
    except Exception:
        return None


def save_wallet(user_data_dir: str, privkey_hex: str, passphrase: Optional[str] = None) -> str:
    """Store (optionally encrypted) private key. Returns the derived address."""
    import time

    if not is_valid_private_key(privkey_hex):
        raise ValueError("Invalid private key")
    privkey_hex = _normalize(privkey_hex)
    address = address_from_private_key(privkey_hex)

    os.makedirs(user_data_dir, exist_ok=True)
    path = _path(user_data_dir)

    if passphrase:
        salt = secrets.token_bytes(16)
        raw = bytes.fromhex(privkey_hex[2:])
        ks = _keystream(salt, passphrase, len(raw))
        ciphertext = _xor(raw, ks)
        check = keccak256(salt + passphrase.encode("utf-8") + b"check").hex()[:16]
        data = {
            "encrypted": True,
            "salt": salt.hex(),
            "ciphertext": ciphertext.hex(),
            "check": check,
            "address": address,
            "created": int(time.time()),
        }
    else:
        data = {
            "encrypted": False,
            "private_key": privkey_hex,
            "address": address,
            "created": int(time.time()),
        }

    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, path)

    global _cached_key
    _cached_key = privkey_hex
    return address


def unlock_wallet(user_data_dir: str, passphrase: Optional[str] = None) -> str:
    """Decrypt (if needed) and cache the key in memory for this session.
    Returns the derived address. Raises ValueError on bad passphrase."""
    p = _path(user_data_dir)
    if not os.path.isfile(p):
        raise ValueError("No wallet connected on this device")
    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)

    global _cached_key
    if not data.get("encrypted"):
        key = data["private_key"]
    else:
        salt = bytes.fromhex(data["salt"])
        check = keccak256(salt + (passphrase or "").encode("utf-8") + b"check").hex()[:16]
        if check != data.get("check"):
            raise ValueError("Wrong passphrase")
        ciphertext = bytes.fromhex(data["ciphertext"])
        ks = _keystream(salt, passphrase or "", len(ciphertext))
        raw = _xor(ciphertext, ks)
        key = "0x" + raw.hex()

    address = address_from_private_key(key)
    if data.get("address") and address.lower() != data["address"].lower():
        raise ValueError("Key/address mismatch")
    _cached_key = key
    return address


def get_cached_key() -> Optional[str]:
    return _cached_key


def is_unlocked() -> bool:
    return _cached_key is not None


def lock_wallet() -> None:
    """Drop the in-memory key (does not delete the stored wallet)."""
    global _cached_key
    _cached_key = None


def disconnect_wallet(user_data_dir: str) -> None:
    """Fully remove the stored wallet from this device."""
    global _cached_key
    _cached_key = None
    p = _path(user_data_dir)
    try:
        if os.path.isfile(p):
            os.remove(p)
    except Exception:
        pass
