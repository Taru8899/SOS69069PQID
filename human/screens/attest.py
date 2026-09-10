from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.metrics import dp

from human.theme import PageScroll, HeaderBar, BrandButton, CopyableText, show_popup, INPUT_BG, TEXT, TEXT_MUTED, TEXT_SEC, GREEN
from human.screens.nav import HumanNavBar
from human import texts as T
from human import record_store as rstore
from human import identity as ident
from human import chain_submit as cs


class HumanAttestScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._page = 0
        root = BoxLayout(orientation="vertical", padding=[dp(10), dp(8), dp(12), dp(8)], spacing=dp(6))
        root.add_widget(HeaderBar(title="ATTEST"))
        scroll = PageScroll()
        mid = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(8), padding=[0, 4, 0, 8])
        mid.bind(minimum_height=mid.setter("height"))
        mid.add_widget(Label(text=T.ATTEST_TITLE, color=TEXT, bold=True, font_size=T.FONT_SECTION, size_hint_y=None, height=dp(28)))
        mid.add_widget(Label(text=T.ATTEST_HINT, color=TEXT_MUTED, font_size=T.FONT_SMALL, size_hint_y=None, height=dp(40)))
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
        self.body = CopyableText(text="", color=TEXT_SEC, height=dp(200))
        mid.add_widget(self.body)
        sub = BrandButton(text="OPTIONAL ON-CHAIN SUBMIT (latest)", bg_color=GREEN)
        sub.bind(on_release=self.submit_latest)
        mid.add_widget(sub)
        scroll.add_widget(mid)
        root.add_widget(scroll)
        root.add_widget(HumanNavBar(current="human_attest"))
        self.add_widget(root)

    def _turn(self, d):
        self._page = max(0, self._page + d)
        self.refresh()

    def on_pre_enter(self, *a):
        self.refresh()

    def refresh(self):
        app = App.get_running_app()
        rows, self._page, pages, total = rstore.list_attests_page(app.user_data_dir, self._page)
        self.page_lbl.text = f"Page {self._page + 1} / {pages}  ({total}, 25/page)"
        if not rows:
            self.body.text = "No attestations yet.\nUse VERIFY to accept someone face-to-face."
            return
        lines = []
        for d in rows:
            subj = d.get("subject") or {}
            lines.append(f"{d.get('_file')}\n  fp={subj.get('fingerprint', '—')}")
        self.body.text = "\n\n".join(lines)

    def submit_latest(self, *_):
        app = App.get_running_app()
        rows = rstore.list_attests(app.user_data_dir)
        if not rows:
            show_popup("Empty", "No attestations")
            return
        subj = rows[0].get("subject") or {}
        fp = (ident.load_identity(app.user_data_dir) or {}).get("fingerprint") or ""
        local = subj.get("fingerprint") or "attest"
        entry = cs.optional_submit(app.user_data_dir, "attest", fp, local)
        show_popup(entry.get("status", "?"), entry.get("tx_hash") or entry.get("error") or str(entry))
