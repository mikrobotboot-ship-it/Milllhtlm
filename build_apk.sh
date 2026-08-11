#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT/android"

echo "=== MikroBot Pro X | GERADOR AUTOMÁTICO DE APK ==="

# Android SDK: usa o já existente no Codespace quando disponível.
if [ -d "${ANDROID_HOME:-}" ]; then
  SDK="$ANDROID_HOME"
elif [ -d "$HOME/Android/Sdk" ]; then
  SDK="$HOME/Android/Sdk"
elif [ -d "/home/codespace/Android/Sdk" ]; then
  SDK="/home/codespace/Android/Sdk"
else
  echo "ERRO: Android SDK não encontrado."
  echo "No seu Codespace, instale/configure o Android SDK e rode novamente."
  exit 1
fi

export ANDROID_HOME="$SDK"
export ANDROID_SDK_ROOT="$SDK"
export PATH="$ANDROID_HOME/platform-tools:$PATH"

echo "SDK: $ANDROID_HOME"

# Se houver Gradle local no projeto, usa-o. Caso contrário, baixa Gradle 8.10.2.
GRADLE="$ROOT/gradle/bin/gradle"
if [ ! -x "$GRADLE" ]; then
  if command -v gradle >/dev/null 2>&1; then
    GRADLE="$(command -v gradle)"
  else
    TMP="$ROOT/.gradle-bootstrap"
    mkdir -p "$TMP"
    ZIP="$TMP/gradle-8.10.2-bin.zip"
    if [ ! -f "$ZIP" ]; then
      echo "Baixando Gradle 8.10.2..."
      curl -fL "https://services.gradle.org/distributions/gradle-8.10.2-bin.zip" -o "$ZIP"
    fi
    if [ ! -x "$TMP/gradle-8.10.2/bin/gradle" ]; then
      unzip -q -o "$ZIP" -d "$TMP"
    fi
    GRADLE="$TMP/gradle-8.10.2/bin/gradle"
  fi
fi

echo "Gradle: $("$GRADLE" --version | grep -m1 '^Gradle ' || true)"
echo "Compilando APK..."

"$GRADLE" assembleDebug --no-daemon

APK="$ROOT/android/app/build/outputs/apk/debug/app-debug.apk"
if [ -f "$APK" ]; then
  echo
  echo "=============================================="
  echo " APK GERADO COM SUCESSO"
  echo " $APK"
  echo "=============================================="
else
  echo "ERRO: APK não foi encontrado após a compilação."
  exit 1
fi
