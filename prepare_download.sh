#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
APK="$ROOT/android/app/build/outputs/apk/debug/app-debug.apk"
if [ ! -f "$APK" ]; then
  echo "APK ainda não existe. Rode ./build_apk.sh primeiro."
  exit 1
fi
cp "$APK" "$ROOT/MikroBot-Pro-X-debug.apk"
echo "APK pronto em:"
echo "$ROOT/MikroBot-Pro-X-debug.apk"
