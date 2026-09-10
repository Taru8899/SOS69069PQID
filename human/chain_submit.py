from __future__ import annotations

def describe_submit_bridge() -> str:
    return (
        "Standalone PQID: export record hash for external submit, "
        "or unlock a gas key when bridge is configured."
    )

def try_get_main_payer_address():
    try:
        from kivy.app import App
        app = App.get_running_app()
        if hasattr(app, "get_payer_key") and app.get_payer_key():
            from sos_core import address_from_private_key
            return address_from_private_key(app.get_payer_key())
    except Exception:
        pass
    return None
