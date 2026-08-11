from kivy.app import App
from kivy.clock import Clock
from kivy.uix.widget import Widget
from jnius import autoclass

class MikroBotApp(App):
    def build(self):
        Clock.schedule_once(self.open_webview, 1.0)
        return Widget()

    def open_webview(self, *_):
        Activity = autoclass("org.kivy.android.PythonActivity").mActivity
        WebView = autoclass("android.webkit.WebView")
        web = WebView(Activity)
        s = web.getSettings()
        s.setJavaScriptEnabled(True)
        s.setDomStorageEnabled(True)
        s.setDatabaseEnabled(True)
        s.setAllowFileAccess(True)
        s.setAllowContentAccess(True)
        web.loadUrl("http://127.0.0.1:8765/")
        Activity.setContentView(web)
        self.webview = web

if __name__ == "__main__":
    MikroBotApp().run()
