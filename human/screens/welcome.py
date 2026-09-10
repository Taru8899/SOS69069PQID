"""Start screen — SOS 69069, motto, create identity + private key on one page."""
from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.metrics import dp
import time

from human.theme import BrandButton, BrandInput, Card, show_popup, PageScroll
from human.app_meta import format_version
from human import texts as T
from human import identity as ident
from pure_crypto import privkey_to_pubkey, keccak256

MOTTO = (
    "Originates from verified Activity and Signatures.\n"
    "Whatever you do. SOS records.\n"
    "Whatever you do. Continue ..."
)
ALG = "secp256k1-interim"
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141


class HumanWelcomeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        root = BoxLayout(orientation="vertical", padding=dp(18), spacing=dp(8))
        scroll = PageScroll()
        mid = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(8), padding=[0, 4, 0, 8])
        mid.bind(minimum_height=mid.setter("height"))

        for text, fs, col, h, bold in (
            ("SOS 69069", dp(24), T.TEXT, dp(36), True),
            ("PQID", dp(16), T.TEXT_SEC, dp(26), False),
            (format_version(), dp(13), T.TEXT_MUTED, dp(22), False),
            ("Activity and Signatures", dp(13), T.TEXT_MUTED, dp(28), False),
        ):
            lbl = Label(text=text, color=col, bold=bold, font_size=fs,
                        size_hint_y=None, height=h, halign="center")
            lbl.bind(size=lambda *a, l=lbl: setattr(l, "text_size", l.size))
            mid.add_widget(lbl)

        motto = Label(
            text=MOTTO, color=T.TEXT_SEC, font_size=dp(13), bold=True,
            size_hint_y=None, height=dp(72), halign="center", valign="middle",
        )
        motto.bind(size=lambda *a: setattr(motto, "text_size", (motto.width, None)))
        mid.add_widget(motto)

        card = Card()
        card.add_widget(Label(
            text="Private key (optional — import existing)",
            color=T.TEXT_MUTED, font_size=dp(12),
            size_hint_y=None, height=dp(22),
        ))
        self.key = BrandInput(hint_text="Private key (0x... or hex)")
        card.add_widget(self.key)

        row = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        create_btn = BrandButton(text="CREATE IDENTITY", bg_color=T.GREEN)
        create_btn.bind(on_release=self.go_create)
        import_btn = BrandButton(text="IMPORT KEY", bg_color=T.BLUE)
        import_btn.bind(on_release=self.do_import)
        row.add_widget(create_btn)
        row.add_widget(import_btn)
        card.add_widget(row)

        enter_btn = BrandButton(text="ENTER PQID", bg_color=T.INPUT_BG)
        enter_btn.bind(on_release=lambda *_: setattr(self.manager, "current", "human_home"))
        card.add_widget(enter_btn)
        mid.add_widget(card)

        scroll.add_widget(mid)
        root.add_widget(scroll)
        self.add_widget(root)

    def go_create(self, *_):
        app = App.get_running_app()
        try:
            if ident.has_identity(app.user_data_dir):
                show_popup("Exists", "Identity already on this device.\nClear human data on PQID to reset.")
                return
            idn = ident.generate_identity()
            ident.save_identity(app.user_data_dir, idn)
            show_popup("Created", f"Fingerprint\n{idn['fingerprint']}")
            self.manager.current = "human_home"
        except Exception as e:
            show_popup("Error", str(e))

    def do_import(self, *_):
        raw = (self.key.text or "").strip().replace("0x", "").replace("0X", "")
        if not raw:
            show_popup("Error", "Paste a private key, or use CREATE IDENTITY.")
            return
        try:
            n = int(raw, 16)
            if not (0 < n < N):
                raise ValueError("out of range")
            x, y = privkey_to_pubkey(n)
            pub_bytes = x.to_bytes(32, "big") + y.to_bytes(32, "big")
            h = keccak256(pub_bytes)
            fp = "-".join(h.hex().upper()[i:i + 4] for i in range(0, 16, 4))
            idn = {
                "protocol": "SOS69069",
                "type": "identity",
                "version": 1,
                "algorithm": ALG,
                "private_key": hex(n),
                "public_key": pub_bytes.hex(),
                "fingerprint": fp,
                "created": int(time.time()),
            }
            app = App.get_running_app()
            ident.save_identity(app.user_data_dir, idn)
            show_popup("Imported", f"Fingerprint\n{fp}")
            self.manager.current = "human_home"
        except Exception as e:
            show_popup("Error", f"Invalid private key.\n{e}")
