from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.metrics import dp

from human.theme import PageScroll, HeaderBar, BrandButton, CopyableText
from human.screens.nav import HumanNavBar
from human import texts as T
from human import identity as ident
from human import wallet_storage as hws


class HumanHomeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        root = BoxLayout(orientation="vertical", padding=[dp(10), dp(8), dp(12), dp(8)], spacing=dp(6))
        root.add_widget(HeaderBar(title="HOME"))
        scroll = PageScroll()
        mid = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(8), padding=[0, 4, 0, 8])
        mid.bind(minimum_height=mid.setter("height"))
        mid.add_widget(Label(text=T.HOME_TITLE, color=T.TEXT, bold=True, font_size=T.FONT_TITLE, size_hint_y=None, height=dp(36), halign="center"))
        self.status = CopyableText(text="", color=T.TEXT_SEC, height=dp(100))
        mid.add_widget(self.status)
        for text, screen, color in (
            (T.BTN_MY_IDENTITY, "human_identity", T.BLUE),
            (T.BTN_MY_RECORDS, "human_records", T.GREEN),
            (T.BTN_VERIFY, "human_verify", T.YELLOW),
            (T.BTN_ATTEST, "human_attest", T.ORANGE),
            (T.BTN_CHAIN, "human_chain", T.BLUE_SOFT),
        ):
            b = BrandButton(text=text, bg_color=color)
            b.bind(on_release=lambda btn, s=screen: setattr(self.manager, "current", s))
            mid.add_widget(b)
        scroll.add_widget(mid)
        root.add_widget(scroll)
        root.add_widget(HumanNavBar(current="human_home"))
        self.add_widget(root)

    def on_pre_enter(self, *a):
        app = App.get_running_app()
        idn = ident.load_identity(app.user_data_dir)
        if not idn:
            self.status.text = "No human identity yet.\nOpen welcome / IDENTITY to create one."
            return
        if not hws.is_unlocked(app.user_data_dir):
            hws.set_unlocked(app.user_data_dir, True, idn)
        self.status.text = (
            f"Fingerprint\n{idn.get('fingerprint', '')}\n\n"
            f"Public key\n{idn.get('public_key', '')}\n\n"
            f"alg: {idn.get('algorithm', '')}\nSession: logged in"
        )
