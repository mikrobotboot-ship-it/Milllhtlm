package com.mikrobot.app;
import android.app.Activity;
import android.os.Bundle;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
public class MainActivity extends Activity {
  public void onCreate(Bundle b){super.onCreate(b); WebView w=new WebView(this); setContentView(w);
    WebSettings s=w.getSettings(); s.setJavaScriptEnabled(true); s.setDomStorageEnabled(true);
    w.setWebViewClient(new WebViewClient()); w.loadUrl("file:///android_asset/index.html");}
}