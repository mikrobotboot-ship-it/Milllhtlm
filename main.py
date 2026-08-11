__version__ = "40.1.0"

from kivy.app import App
from kivy.clock import Clock
from kivy.uix.widget import Widget
from jnius import autoclass

PACKAGE = "br.mikrobot.mikrobotprox"

class MikroBotApp(App):
    def build(self):
        Clock.schedule_once(self.start_core, 0.4)
        Clock.schedule_once(self.open_webview, 1.6)
        return Widget()

    def start_core(self, *_):
        try:
            Activity = autoclass("org.kivy.android.PythonActivity").mActivity
            Service = autoclass(PACKAGE + ".ServiceMikrobotcore")
            service = Service()
            service.start(Activity, "")
            try:
                service.setAutoRestartService(True)
            except Exception:
                pass
            self.core_started = True
        except Exception as exc:
            self.core_started = False
            print("MikroBot Core start error:", exc)

    def open_webview(self, *_):
        Activity = autoclass("org.kivy.android.PythonActivity").mActivity
        WebView = autoclass("android.webkit.WebView")
        web = WebView(Activity)
        settings = web.getSettings()
        settings.setJavaScriptEnabled(True)
        settings.setDomStorageEnabled(True)
        settings.setDatabaseEnabled(True)
        settings.setAllowFileAccess(True)
        settings.setAllowContentAccess(True)
        web.loadUrl("http://127.0.0.1:8765/")
        Activity.setContentView(web)
        self.webview = web

if __name__ == "__main__":
    MikroBotApp().run()
