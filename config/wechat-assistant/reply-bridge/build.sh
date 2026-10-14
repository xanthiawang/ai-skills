#!/bin/bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
task_root="$HOME/.local/share/wechat-assistant"
app="$task_root/ReplyBridge.app"
if [[ -e "$app" ]]; then echo 'App already exists; preserve existing signed binary and permission state.'; exit 1; fi
umask 077
mkdir -p "$app/Contents/MacOS" "$app/Contents/Resources"
xcrun swiftc -parse-as-library -O -target arm64-apple-macosx14.0 Capture.swift Send.swift Main.swift -o "$app/Contents/MacOS/ReplyBridge"
/usr/bin/python3 - "$app" <<'PY'
import plistlib,sys
from pathlib import Path
app=Path(sys.argv[1]);p=app/'Contents/Info.plist'
with p.open('wb') as f:
    plistlib.dump({'CFBundleIdentifier':'io.github.xanthiawang.wechat-reply-bridge',
      'CFBundleName':'WeChat Reply Bridge','CFBundleDisplayName':'微信回复确认',
      'CFBundleExecutable':'ReplyBridge','CFBundlePackageType':'APPL',
      'CFBundleShortVersionString':'0.1.0','LSMinimumSystemVersion':'14.0',
      'NSHighResolutionCapable':True},f)
PY
codesign --force --sign - "$app"
codesign --verify --deep --strict "$app"
echo "Built native confirmation app: $app"
