from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.metrics import dp
import json

from human.theme import PageScroll, HeaderBar, BrandButton, CopyableText, show_popup, INPUT_BG, TEXT, TEXT_MUTED, TEXT_SEC, GREEN
from human.screens.nav import HumanNavBar
from human import texts as T
from human import attestation as att


class HumanVerifyScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        root = BoxLayout(orientation="vertical", padding=[dp(10), dp(8), dp(12), dp(8)], spacing=dp(6))
        root.add_widget(HeaderBar(title="VERIFY"))
        scroll = PageScroll()
        mid = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(8), padding=[0, 4, 0, 8])
        mid.bind(minimum_height=mid.setter("height"))
        mid.add_widget(Label(text=T.VERIFY_TITLE, color=TEXT, bold=True, font_size=T.FONT_SECTION, size_hint_y=None, height=dp(28)))
        mid.add_widget(Label(text=T.VERIFY_HINT, color=TEXT_MUTED, font_size=T.FONT_SMALL, size_hint_y=None, height=dp(48)))

        # Plain TextInput so Android long-press paste works
        self.paste = TextInput(
            text="",
            hint_text='{"type":"identity","pk":"...","fingerprint":"..."}',
            multiline=True,
            readonly=False,
            size_hint_y=None,
            height=dp(140),
            background_normal="",
            background_active="",
            background_color=INPUT_BG,
            foreground_color=TEXT,
            cursor_color=TEXT,
            padding=[dp(12), dp(12)],
            font_size=dp(14),
            write_tab=False,
        )
        mid.add_widget(self.paste)

        self.info = CopyableText(text="", color=TEXT_SEC, height=dp(80))
        mid.add_widget(self.info)
        parse_b = BrandButton(text=T.VERIFY_PARSE, bg_color=INPUT_BG)
        parse_b.bind(on_release=self.parse)
        mid.add_widget(parse_b)
        acc = BrandButton(text=T.VERIFY_ACCEPT, bg_color=GREEN)
        acc.bind(on_release=self.accept)
        mid.add_widget(acc)
        scroll.add_widget(mid)
        root.add_widget(scroll)
        root.add_widget(HumanNavBar(current="human_verify"))
        self.add_widget(root)
        self._parsed = None

    def on_pre_enter(self, *a):
        # Focus field so keyboard / paste menu is available
        try:
            self.paste.focus = True
        except Exception:
            pass

    def parse(self, *_):
        try:
            data = json.loads((self.paste.text or "").strip())
            if "fingerprint" not in data and data.get("type") != "identity":
                raise ValueError("Need identity JSON with fingerprint")
            self._parsed = data
            self.info.text = (
                f"Fingerprint\n{data.get('fingerprint', '—')}\n"
                f"pk: {(data.get('pk') or data.get('public_key') or '')}"
            )
        except Exception as e:
            self._parsed = None
            show_popup("Error", str(e))

    def accept(self, *_):
        if not self._parsed:
            self.parse()
            if not self._parsed:
                return
        app = App.get_running_app()
        att.save_acceptance(app.user_data_dir, self._parsed)
        show_popup("Accepted", "Stored local face-to-face acceptance.")
