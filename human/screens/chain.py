from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.metrics import dp

from human.theme import PageScroll, HeaderBar, BrandButton, CopyableText, show_popup
from human.screens.nav import HumanNavBar
from human import texts as T
from human import chain_submit as cs
from human import record_store as rstore
from human import wallet_storage as hws


class HumanChainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        root = BoxLayout(orientation="vertical", padding=[dp(10), dp(8), dp(12), dp(8)], spacing=dp(6))
        root.add_widget(HeaderBar(title="CHAIN"))
        scroll = PageScroll()
        mid = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(8), padding=[0, 4, 0, 8])
        mid.bind(minimum_height=mid.setter("height"))
        mid.add_widget(Label(text=T.CHAIN_TITLE, color=T.TEXT, bold=True, font_size=T.FONT_SECTION, size_hint_y=None, height=dp(28)))
        mid.add_widget(Label(
            text="Records are signed by human identity.\nOn-chain gas uses whatever Ethereum wallet is connected at submit time (main app payer when embedded).",
            color=T.TEXT_MUTED, font_size=T.FONT_SMALL, size_hint_y=None, height=dp(64),
        ))
        self.body = CopyableText(text="", color=T.TEXT_SEC, height=dp(160))
        mid.add_widget(self.body)
        mid.add_widget(Label(text="Latest local record hashes (copyable)", color=T.TEXT_MUTED, font_size=T.FONT_SMALL, size_hint_y=None, height=dp(22)))
        self.hashes = CopyableText(text="", color=T.GREEN_BR, height=dp(120))
        mid.add_widget(self.hashes)
        scroll.add_widget(mid)
        root.add_widget(scroll)
        root.add_widget(HumanNavBar(current="human_chain"))
        self.add_widget(root)

    def on_pre_enter(self, *a):
        app = App.get_running_app()
        addr = cs.try_get_main_payer_address()
        sess = "logged in" if hws.is_unlocked(app.user_data_dir) else "logged out"
        self.body.text = (
            cs.describe_submit_bridge()
            + f"\n\nHuman session: {sess}\n"
            + (f"Gas payer (connected now): {addr}" if addr else "Gas payer: none connected (standalone or unlock main wallet)")
        )
        rows = rstore.list_records(app.user_data_dir)[:10]
        if not rows:
            self.hashes.text = "(no local records yet)"
        else:
            self.hashes.text = "\n".join(f"{r.get('id')}: {r.get('hash')}" for r in rows)
