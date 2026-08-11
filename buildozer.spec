[app]
title = MikroBot Pro X V55
package.name = mikrobotprox
package.domain = br.mikrobot
source.dir = .
source.include_exts = py,html,txt
source.include_patterns = assets/*
version = 5.5.1
requirements = python3,kivy,pyjnius
orientation = portrait
android.api = 35
android.minapi = 26
android.archs = arm64-v8a
android.permissions = INTERNET,ACCESS_NETWORK_STATE,FOREGROUND_SERVICE,FOREGROUND_SERVICE_SPECIAL_USE,POST_NOTIFICATIONS
services = mikrobotcore:service.py:foreground:sticky

[buildozer]
log_level = 2
warn_on_root = 1
