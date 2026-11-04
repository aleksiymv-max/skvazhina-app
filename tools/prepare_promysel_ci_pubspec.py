#!/usr/bin/env python3
"""Add unchanged, pinned CI-only dependencies before one Flutter pub resolution.

The existing repo starts with a frozen Flutter source ZIP; this avoids calling
`flutter pub add` multiple times per CI run (each runs dependency resolution).
"""
from pathlib import Path
import sys

if len(sys.argv) != 2 or sys.argv[1] not in ("web", "android"):
    raise SystemExit("Usage: prepare_promysel_ci_pubspec.py web|android")
target = sys.argv[1]
p = Path("pubspec.yaml")
s = p.read_text(encoding="utf-8")
if target == "web" and "\n  sqflite_common_ffi_web:" not in s:
    anchor = "\ndev_dependencies:\n"
    assert s.count(anchor) == 1, "dependencies anchor changed"
    s = s.replace(anchor, "\n  sqflite_common_ffi_web: ^1.2.0\n" + anchor, 1)
if "\n  sqflite_common_ffi:" not in s:
    anchor = "\nflutter:\n"
    assert s.count(anchor) == 1, "dev_dependencies anchor changed"
    s = s.replace(anchor, "\n  sqflite_common_ffi: ^2.3.6\n" + anchor, 1)
assert "\n  sqflite_common_ffi: ^2.3.6\n" in s
if target == "web":
    assert "\n  sqflite_common_ffi_web: ^1.2.0\n" in s
p.write_text(s, encoding="utf-8")
print("PASS: CI dependencies declared for", target, "with one pub get")
