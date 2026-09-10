from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.metrics import dp
import json

from human.theme import PageScroll, HeaderBar, BrandButton, CopyableText, Card, show_popup
from human.screens.nav import HumanNavBar
from human import texts as T
from human import identity as ident
from human import record as rec
from human import record_store as rstore
from human import wallet_storage as hws


class HumanRecordsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        root = BoxLayout(orientation="vertical", padding=[dp(10), dp(8), dp(12), dp(8)], spacing=dp(6))
        root.add_widget(HeaderBar(title="RECORDS"))
        scroll = PageScroll()
        mid = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(8), padding=[0, 4, 0, 8])
        mid.bind(minimum_height=mid.setter("height"))
        mid.add_widget(Label(text=T.RECORDS_TITLE, color=T.TEXT, bold=True, font_size=T.FONT_SECTION, size_hint_y=None, height=dp(28)))
        create = BrandButton(text=T.RECORDS_CREATE, bg_color=T.BLUE)
        create.bind(on_release=self.create_rec)
        mid.add_widget(create)
        self.list_box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(6))
        self.list_box.bind(minimum_height=self.list_box.setter("height"))
        mid.add_widget(self.list_box)
        scroll.add_widget(mid)
        root.add_widget(scroll)
        root.add_widget(HumanNavBar(current="human_records"))
        self.add_widget(root)

    def on_pre_enter(self, *a):
        self.refresh()

    def refresh(self):
        self.list_box.clear_widgets()
        app = App.get_running_app()
        rows = rstore.list_records(app.user_data_dir)
        if not rows:
            self.list_box.add_widget(Label(text=T.RECORDS_EMPTY, color=T.TEXT_MUTED, size_hint_y=None, height=dp(28)))
            return
        for r in rows[:30]:
            card = Card()
            body = (
                f"{r.get('id', '—')}\n"
                f"{r.get('activity_type', '')}\n"
                f"hash={r.get('hash', '')}"
            )
            card.add_widget(CopyableText(text=body, color=T.TEXT_SEC, height=dp(80)))
            self.list_box.add_widget(card)

    def create_rec(self, *_):
        app = App.get_running_app()
        if not hws.is_unlocked(app.user_data_dir):
            # restore if file exists
            idn = ident.load_identity(app.user_data_dir)
            if idn:
                hws.set_unlocked(app.user_data_dir, True, idn)
            else:
                show_popup("Not logged in", "Create or import identity on welcome first.")
                self.manager.current = "human_welcome"
                return
        idn = ident.load_identity(app.user_data_dir)
        if not idn:
            show_popup("Need identity", "Create human identity first.")
            self.manager.current = "human_identity"
            return
        body = rec.build_record(idn["public_key"], "presence", 1)
        h = rec.record_hash(body)
        entry = {
            "id": "69069-" + body["serial"][:8].upper(),
            "hash": h,
            "activity_type": "presence",
            "record": body,
            "state": "SIGNED_LOCAL",
            "issuer_fingerprint": idn.get("fingerprint"),
        }
        rstore.save_record(app.user_data_dir, entry)
        show_popup("Record saved", f"{entry['id']}\n{h}")
        self.refresh()
