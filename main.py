"""SOS 69069 PQID — standalone entry point."""
import os
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager

from human.app_meta import APP_NAME, format_version
from human.screens.loading import HumanLoadingScreen
from human.screens.home import HumanHomeScreen
from human.screens.identity import HumanIdentityScreen
from human.screens.verify import HumanVerifyScreen
from human.screens.records import HumanRecordsScreen
from human.screens.attest import HumanAttestScreen
from human.screens.chain import HumanChainScreen
from human.screens.pqid import HumanPqidScreen


class PQIDApp(App):
    """Standalone SOS 69069 PQID."""
    private_key = None  # no eth session required
    keys = None
    sm = None
    pqid_after_load = "human_home"

    def get_payer_key(self):
        return None

    def build(self):
        os.makedirs(self.user_data_dir, exist_ok=True)
        self.title = APP_NAME
        sm = ScreenManager()
        self.sm = sm
        for name, cls in (
            ("human_loading", HumanLoadingScreen),
            ("human_home", HumanHomeScreen),
            ("human_identity", HumanIdentityScreen),
            ("human_verify", HumanVerifyScreen),
            ("human_records", HumanRecordsScreen),
            ("human_attest", HumanAttestScreen),
            ("human_chain", HumanChainScreen),
            ("human_pqid", HumanPqidScreen),
        ):
            sm.add_widget(cls(name=name))
        sm.current = "human_loading"
        return sm


if __name__ == "__main__":
    PQIDApp().run()
