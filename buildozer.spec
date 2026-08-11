[app]
title = MikroBot Pro X Rebuild 40K
package.name = mikrobotprox
package.domain = br.mikrobot
source.dir = .
source.include_exts = py,html,txt,json,xml
source.include_patterns = assets/*,android/*
source.exclude_dirs = bin,.buildozer,.git,__pycache__,tests
version = 40.1.0
requirements = python3,kivy,pyjnius
orientation = portrait
android.api = 35
android.minapi = 24
android.archs = arm64-v8a
android.permissions = INTERNET,ACCESS_NETWORK_STATE,FOREGROUND_SERVICE,FOREGROUND_SERVICE_SPECIAL_USE,POST_NOTIFICATIONS
android.extra_manifest_application_arguments = ./android/manifest_application.xml
services = mikrobotcore:service.py:foreground:sticky:foregroundServiceType=specialUse

[buildozer]
log_level = 2
android.accept_sdk_license = True
