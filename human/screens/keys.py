from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.metrics import dp

from human.theme import (
    PageScroll, HeaderBar, BrandButton, BrandInput, CopyableText, show_popup,
    TEXT, TEXT_SEC, TEXT_MUTED, GREEN, GREEN_BR, BLUE, ORANGE, DANGER, INPUT_BG,
)
from human.screens.nav import HumanNavBar
from human import keys as ekeys
from human import metrics as met
from kivy.clock import Clock


class HumanWalletScreen(Screen):
    """Optional: connect an Ethereum wallet used only to sign + pay gas for
    the user's own optional on-chain submits. Nothing here is required —
    everything else in the app works with zero wallet connected."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        root = BoxLayout(orientation="vertical", padding=[dp(10), dp(8), dp(12), dp(8)], spacing=dp(6))
        root.add_widget(HeaderBar(title="WALLET"))
        scroll = PageScroll()
        mid = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(8), padding=[0, 4, 0, 8])
        mid.bind(minimum_height=mid.setter("height"))

        mid.add_widget(Label(
            text="CONNECT WALLET (OPTIONAL)", color=TEXT, bold=True,
            font_size=dp(16), size_hint_y=None, height=dp(28),
        ))
        mid.add_widget(Label(
            text=(
                "Only needed if you want to submit an optional record to the\n"
                "SOS contract on-chain. Everything else in this app works\n"
                "without a wallet. The key stays on this device."
            ),
            color=TEXT_MUTED, font_size=dp(12), size_hint_y=None, height=dp(56),
        ))

        self.status = CopyableText(text="", color=TEXT_SEC, height=dp(64))
        mid.add_widget(self.status)

        mid.add_widget(Label(
            text="Metrics for connected address (Push = signer, Trust = intendedTo)",
            color=TEXT_MUTED, font_size=dp(11), size_hint_y=None, height=dp(20),
        ))
        self.metrics = CopyableText(text="", color=TEXT_SEC, height=dp(120))
        mid.add_widget(self.metrics)
        ref_b = BrandButton(text="REFRESH METRICS (+ CHAIN PQID CHECK)", bg_color=INPUT_BG)
        ref_b.bind(on_release=self.refresh_metrics)
        mid.add_widget(ref_b)

        mid.add_widget(Label(text="Passphrase (optional, encrypts key at rest)", color=TEXT_MUTED,
                              font_size=dp(11), size_hint_y=None, height=dp(18)))
        self.pass_in = BrandInput(password=True, hint_text="leave blank for none")
        mid.add_widget(self.pass_in)

        mid.add_widget(Label(text="Import existing private key (0x + 64 hex chars)", color=TEXT_MUTED,
                              font_size=dp(11), size_hint_y=None, height=dp(18)))
        self.key_in = BrandInput(password=True, hint_text="0x...")
        mid.add_widget(self.key_in)

        import_b = BrandButton(text="IMPORT WALLET", bg_color=BLUE)
        import_b.bind(on_release=self.import_wallet)
        mid.add_widget(import_b)

        gen_b = BrandButton(text="GENERATE NEW WALLET", bg_color=GREEN)
        gen_b.bind(on_release=self.generate_wallet)
        mid.add_widget(gen_b)

        unlock_b = BrandButton(text="UNLOCK CONNECTED WALLET", bg_color=ORANGE)
        unlock_b.bind(on_release=self.unlock_wallet)
        mid.add_widget(unlock_b)

        disc_b = BrandButton(text="DISCONNECT / REMOVE WALLET", bg_color=DANGER)
        disc_b.bind(on_release=self.disconnect_wallet)
        mid.add_widget(disc_b)

        mid.add_widget(Label(
            text=(
                "Warning: whoever holds this key can sign and pay gas as this\n"
                "address. Back up a generated key immediately — it is shown\n"
                "once and is not recoverable if lost."
            ),
            color=TEXT_MUTED, font_size=dp(11), size_hint_y=None, height=dp(50),
        ))

        scroll.add_widget(mid)
        root.add_widget(scroll)
        root.add_widget(HumanNavBar(current="human_wallet"))
        self.add_widget(root)

    def on_pre_enter(self, *a):
        self.refresh()

    def refresh(self):
        app = App.get_running_app()
        meta = ekeys.get_wallet_meta(app.user_data_dir)
        if not meta:
            self.status.text = "No wallet connected.\nImport a key or generate a new one below."
            self.metrics.text = "Connect and unlock a wallet to load Push / Trust / Effective."
            return
        lock_state = "unlocked (ready to submit)" if ekeys.is_unlocked() else "locked (tap UNLOCK before submitting)"
        prot = "passphrase-protected" if meta.get("encrypted") else "no passphrase set"
        self.status.text = (
            f"Connected: {meta.get('address')}\n"
            f"{prot} — {lock_state}"
        )
        self.metrics.text = "Loading metrics…"
        Clock.schedule_once(lambda dt: self._load_metrics(meta.get("address")), 0.05)

    def _clear_inputs(self):
        self.key_in.text = ""
        self.pass_in.text = ""

    def import_wallet(self, *_):
        app = App.get_running_app()
        raw = (self.key_in.text or "").strip()
        passphrase = (self.pass_in.text or "").strip() or None
        if not ekeys.is_valid_private_key(raw):
            show_popup("Invalid key", "Expected 0x + 64 hex characters.")
            return
        try:
            address = ekeys.save_wallet(app.user_data_dir, raw, passphrase)
            self._clear_inputs()
            show_popup("Wallet connected", f"Address:\n{address}")
            self.refresh()
        except Exception as e:
            show_popup("Error", str(e))

    def generate_wallet(self, *_):
        app = App.get_running_app()
        if ekeys.has_wallet(app.user_data_dir):
            show_popup("Already connected", "Disconnect the current wallet first.")
            return
        passphrase = (self.pass_in.text or "").strip() or None
        priv = ekeys.generate_private_key()
        try:
            address = ekeys.save_wallet(app.user_data_dir, priv, passphrase)
            self._clear_inputs()
            show_popup(
                "Wallet generated — BACK THIS UP NOW",
                f"Address:\n{address}\n\nPrivate key (shown once):\n{priv}",
            )
            self.refresh()
        except Exception as e:
            show_popup("Error", str(e))

    def unlock_wallet(self, *_):
        app = App.get_running_app()
        passphrase = (self.pass_in.text or "").strip() or None
        try:
            address = ekeys.unlock_wallet(app.user_data_dir, passphrase)
            self.pass_in.text = ""
            show_popup("Unlocked", f"Ready to submit as:\n{address}")
            self.refresh()
        except Exception as e:
            show_popup("Error", str(e))

    def disconnect_wallet(self, *_):
        app = App.get_running_app()
        ekeys.disconnect_wallet(app.user_data_dir)
        self._clear_inputs()
        show_popup("Disconnected", "Wallet removed from this device.")
        self.refresh()

    def refresh_metrics(self, *_):
        app = App.get_running_app()
        meta = ekeys.get_wallet_meta(app.user_data_dir)
        if not meta or not meta.get("address"):
            show_popup("No wallet", "Connect a wallet first.")
            return
        self.metrics.text = "Refreshing (chain PQID scan may take a few seconds)…"
        Clock.schedule_once(lambda dt: self._load_metrics(meta.get("address"), chain_check=True), 0.05)

    def _load_metrics(self, address, chain_check=False):
        app = App.get_running_app()
        lines = []
        # 1) Full on-chain contract stats
        try:
            onchain = met.stats_onchain(address)
            lines.append(met.format_block("On-chain (SOS contract)", onchain))
        except Exception as e:
            lines.append(f"On-chain (SOS contract)\n  (error: {e})")
        # 2) PQID local log
        try:
            local = met.stats_pqid_local(app.user_data_dir, address)
            lines.append(met.format_block("PQID only (local log)", local))
        except Exception as e:
            lines.append(f"PQID only (local log)\n  (error: {e})")
        # 3) Optional chain cross-check
        if chain_check:
            try:
                chain = met.stats_pqid_chain(address)
                lines.append(met.format_block("PQID only (chain cross-check)", chain))
            except Exception as e:
                lines.append(f"PQID only (chain cross-check)\n  (error: {e})")
        else:
            lines.append("PQID only (chain cross-check)\n  Tap REFRESH METRICS to scan SignatureRecorded logs (metadata PQID|).")
        self.metrics.text = "\n\n".join(lines)
