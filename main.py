"""SOS 69069 PQID — standalone entry point."""
import os
import traceback

os.environ.setdefault("KIVY_GL_BACKEND", "sdl2")

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.metrics import dp

from human.app_meta import APP_NAME


class PQIDApp(App):
    private_key = None
    keys = None
    sm = None

    def get_payer_key(self):
        return None

    def build(self):
        try:
            os.makedirs(self.user_data_dir, exist_ok=True)
        except Exception:
            pass
        self.title = APP_NAME
        # restore human session if identity file present
        try:
            from human import identity as ident
            from human import wallet_storage as hws
            hws.restore_session(self.user_data_dir, ident.load_identity)
        except Exception:
            traceback.print_exc()

        sm = ScreenManager()
        self.sm = sm

        screen_specs = [
            ("human_welcome", "human.screens.welcome", "HumanWelcomeScreen"),
            ("human_home", "human.screens.home", "HumanHomeScreen"),
            ("human_identity", "human.screens.identity", "HumanIdentityScreen"),
            ("human_verify", "human.screens.verify", "HumanVerifyScreen"),
            ("human_records", "human.screens.records", "HumanRecordsScreen"),
            ("human_attest", "human.screens.attest", "HumanAttestScreen"),
            ("human_chain", "human.screens.chain", "HumanChainScreen"),
            ("human_pqid", "human.screens.pqid", "HumanPqidScreen"),
        ]
        loaded = []
        errors = []
        for name, modpath, clsname in screen_specs:
            try:
                import importlib
                mod = importlib.import_module(modpath)
                cls = getattr(mod, clsname)
                sm.add_widget(cls(name=name))
                loaded.append(name)
            except Exception as e:
                errors.append(f"{name}: {e}")
                traceback.print_exc()

        if not loaded:
            box = BoxLayout(orientation="vertical", padding=dp(20))
            box.add_widget(Label(
                text="SOS 69069 PQID\nFailed to load:\n" + "\n".join(errors[:5]),
                color=(1, 1, 1, 1),
            ))
            return box

        # If already logged in, go HOME; else welcome
        try:
            from human import wallet_storage as hws
            if hws.is_unlocked(self.user_data_dir) and "human_home" in loaded:
                sm.current = "human_home"
            else:
                sm.current = "human_welcome" if "human_welcome" in loaded else loaded[0]
        except Exception:
            sm.current = loaded[0]
        return sm


if __name__ == "__main__":
    try:
        PQIDApp().run()
    except Exception:
        traceback.print_exc()
        raise
