from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.metrics import dp

from human.theme import PageScroll, HeaderBar, BrandButton, CopyableText, show_popup, INPUT_BG, TEXT, TEXT_MUTED, TEXT_SEC, GREEN, GREEN_BR
from human.screens.nav import HumanNavBar
from human import texts as T
from human import chain_submit as cs
from human import submit_log as slog
from human import identity as ident
from human import wallet_storage as hws
from human import record_store as rstore
from human import keys as ekeys


class HumanChainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._page = 0
        root = BoxLayout(orientation="vertical", padding=[dp(10), dp(8), dp(12), dp(8)], spacing=dp(6))
        root.add_widget(HeaderBar(title="CHAIN"))
        scroll = PageScroll()
        mid = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(8), padding=[0, 4, 0, 8])
        mid.bind(minimum_height=mid.setter("height"))
        mid.add_widget(Label(text=T.CHAIN_TITLE, color=TEXT, bold=True, font_size=T.FONT_SECTION, size_hint_y=None, height=dp(28)))
        mid.add_widget(Label(
            text="Contract metrics: Push=signer count, Trust=intendedTo count,\nEffective=Trust−Push (live). Overflow wraps counters only.",
            color=TEXT_MUTED, font_size=T.FONT_SMALL, size_hint_y=None, height=dp(48),
        ))
        self.metrics = CopyableText(text="", color=TEXT_SEC, height=dp(72))
        mid.add_widget(self.metrics)
        self.body = CopyableText(text="", color=TEXT_SEC, height=dp(100))
        mid.add_widget(self.body)
        self.page_lbl = Label(text="", color=TEXT_MUTED, size_hint_y=None, height=dp(22))
        mid.add_widget(self.page_lbl)
        nav = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8))
        prev_b = BrandButton(text="PREV", bg_color=INPUT_BG)
        prev_b.bind(on_release=lambda *_: self._turn(-1))
        next_b = BrandButton(text="NEXT", bg_color=INPUT_BG)
        next_b.bind(on_release=lambda *_: self._turn(1))
        nav.add_widget(prev_b)
        nav.add_widget(next_b)
        mid.add_widget(nav)
        self.hashes = CopyableText(text="", color=GREEN_BR, height=dp(160))
        mid.add_widget(self.hashes)
        wallet_b = BrandButton(text="CONNECT / MANAGE WALLET", bg_color=INPUT_BG)
        wallet_b.bind(on_release=self.go_wallet)
        mid.add_widget(wallet_b)
        sub = BrandButton(text="OPTIONAL SUBMIT LATEST RECORD", bg_color=GREEN)
        sub.bind(on_release=self.submit_latest)
        mid.add_widget(sub)
        scroll.add_widget(mid)
        root.add_widget(scroll)
        root.add_widget(HumanNavBar(current="human_chain"))
        self.add_widget(root)

    def _turn(self, d):
        self._page = max(0, self._page + d)
        self.refresh()

    def on_pre_enter(self, *a):
        self.refresh()

    def refresh(self):
        app = App.get_running_app()
        counts = slog.local_kind_counts(app.user_data_dir)
        self.metrics.text = (
            f"Local PQID submitted log — Trust-kinds: {counts['trust']}  "
            f"Push-kinds: {counts['push']}  Effective(submitted): {counts['effective']}\n"
            f"(On-chain for an eth address: contract statsOf / effectiveOf)"
        )
        addr = cs.try_get_main_payer_address()
        sess = "logged in" if hws.is_unlocked(app.user_data_dir) else "logged out"
        meta = ekeys.get_wallet_meta(app.user_data_dir)
        if not meta:
            wstate = "no wallet connected — tap CONNECT / MANAGE WALLET"
        elif not ekeys.is_unlocked():
            wstate = "wallet connected but locked — tap CONNECT / MANAGE WALLET to unlock"
        else:
            wstate = "wallet connected + unlocked, ready to submit"
        self.body.text = (
            cs.describe_submit_bridge()
            + f"\nHuman session: {sess}\nWallet: {wstate}\nGas payer: {addr or '(none)'}"
        )
        rows, self._page, pages, total = slog.page(app.user_data_dir, self._page)
        self.page_lbl.text = f"Submit log page {self._page + 1} / {pages} ({total})"
        if not rows:
            self.hashes.text = "(no submits yet)"
        else:
            lines = []
            for r in rows:
                lines.append(
                    f"{r.get('status')} {r.get('kind')} tx={r.get('tx_hash') or '—'}\n"
                    f"  meta={r.get('metadata') or ''}\n  ph={r.get('payload_hash') or ''}"
                )
            self.hashes.text = "\n".join(lines)

    def go_wallet(self, *_):
        App.get_running_app().sm.current = "human_wallet"

    def submit_latest(self, *_):
        app = App.get_running_app()
        if not ekeys.get_cached_key() and not cs.try_get_main_payer_key():
            show_popup(
                "No wallet",
                "Connect and unlock a wallet first (CONNECT / MANAGE WALLET) "
                "— on-chain submit is optional and needs a gas payer.",
            )
            return
        recs = rstore.list_records(app.user_data_dir)
        if not recs:
            show_popup("Empty", "Create a record first")
            return
        h = recs[0].get("hash") or ""
        fp = (ident.load_identity(app.user_data_dir) or {}).get("fingerprint") or ""
        entry = cs.optional_submit(app.user_data_dir, "chain", fp, h)
        show_popup(entry.get("status", "?"), entry.get("tx_hash") or entry.get("error") or str(entry))
        self.refresh()
