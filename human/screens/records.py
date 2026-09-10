from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.metrics import dp

from human.theme import PageScroll, HeaderBar, BrandButton, CopyableText, Card, show_popup, INPUT_BG, GREEN, BLUE, TEXT, TEXT_MUTED, TEXT_SEC
from human.screens.nav import HumanNavBar
from human import texts as T
from human import identity as ident
from human import record as rec
from human import record_store as rstore
from human import wallet_storage as hws
from human import chain_submit as cs


class HumanRecordsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._page = 0
        root = BoxLayout(orientation="vertical", padding=[dp(10), dp(8), dp(12), dp(8)], spacing=dp(6))
        root.add_widget(HeaderBar(title="RECORDS"))
        scroll = PageScroll()
        mid = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(8), padding=[0, 4, 0, 8])
        mid.bind(minimum_height=mid.setter("height"))
        mid.add_widget(Label(text=T.RECORDS_TITLE, color=TEXT, bold=True, font_size=T.FONT_SECTION, size_hint_y=None, height=dp(28)))
        create = BrandButton(text=T.RECORDS_CREATE, bg_color=BLUE)
        create.bind(on_release=self.create_rec)
        mid.add_widget(create)
        self.page_lbl = Label(text="", color=TEXT_MUTED, size_hint_y=None, height=dp(22))
        mid.add_widget(self.page_lbl)
        nav = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8))
        prev_b = BrandButton(text="PREV", bg_color=INPUT_BG)
        prev_b.bind(on_release=self.prev_page)
        next_b = BrandButton(text="NEXT", bg_color=INPUT_BG)
        next_b.bind(on_release=self.next_page)
        nav.add_widget(prev_b)
        nav.add_widget(next_b)
        mid.add_widget(nav)
        self.list_box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(6))
        self.list_box.bind(minimum_height=self.list_box.setter("height"))
        mid.add_widget(self.list_box)
        scroll.add_widget(mid)
        root.add_widget(scroll)
        root.add_widget(HumanNavBar(current="human_records"))
        self.add_widget(root)
        self._last_hash = None
        self._last_fp = None

    def on_pre_enter(self, *a):
        self.refresh()

    def prev_page(self, *_):
        self._page = max(0, self._page - 1)
        self.refresh()

    def next_page(self, *_):
        self._page += 1
        self.refresh()

    def refresh(self):
        self.list_box.clear_widgets()
        app = App.get_running_app()
        rows, self._page, pages, total = rstore.list_records_page(app.user_data_dir, self._page)
        self.page_lbl.text = f"Page {self._page + 1} / {pages}  ({total} records, 25/page)"
        if not rows:
            self.list_box.add_widget(Label(text=T.RECORDS_EMPTY, color=TEXT_MUTED, size_hint_y=None, height=dp(28)))
            return
        for r in rows:
            card = Card()
            body = f"{r.get('id', '—')}\n{r.get('activity_type', '')}\nhash={r.get('hash', '')}"
            card.add_widget(CopyableText(text=body, color=TEXT_SEC, height=dp(72)))
            sub = BrandButton(text="OPTIONAL ON-CHAIN SUBMIT", bg_color=GREEN)
            hid = r.get("hash") or ""
            sub.bind(on_release=lambda b, h=hid: self.submit_one(h))
            card.add_widget(sub)
            self.list_box.add_widget(card)

    def create_rec(self, *_):
        app = App.get_running_app()
        idn = ident.load_identity(app.user_data_dir)
        if not idn:
            show_popup("Need identity", "Create human identity first.")
            self.manager.current = "human_identity"
            return
        if not hws.is_unlocked(app.user_data_dir):
            hws.set_unlocked(app.user_data_dir, True, idn)
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
        self._last_hash = h
        self._last_fp = idn.get("fingerprint")
        show_popup("Record saved", f"{entry['id']}\n{h}")
        self.refresh()

    def submit_one(self, local_hash):
        app = App.get_running_app()
        idn = ident.load_identity(app.user_data_dir) or {}
        fp = idn.get("fingerprint") or ""
        entry = cs.optional_submit(app.user_data_dir, "record", fp, local_hash)
        if entry.get("status") == "submitted":
            show_popup("Submitted", f"tx\n{entry.get('tx_hash')}\n{entry.get('metadata')}")
        else:
            show_popup(entry.get("status", "result"), entry.get("error") or str(entry))
