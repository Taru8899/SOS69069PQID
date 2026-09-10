_session_unlocked = False

def set_unlocked(v: bool):
    global _session_unlocked
    _session_unlocked = bool(v)

def is_unlocked() -> bool:
    return _session_unlocked

def logout_session():
    set_unlocked(False)
