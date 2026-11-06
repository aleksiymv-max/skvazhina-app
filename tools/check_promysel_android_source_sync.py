#!/usr/bin/env python3
"""Source parity check without building Android or consuming Android CI minutes.

Android uses the same zipped Flutter base and patch chain as Web. The archived
Android recipe is a non-executable reference, NOT an active GitHub workflow.
Every functional frontend script added to Web must also be added to that
reference, ensuring Android source stays ready for later manual APK building.
"""
from pathlib import Path
import re

web_file=Path(".github/workflows/web-ios.yml")
android_archive=Path("tools/archive/android-build.workflow.yml.txt")
assert web_file.exists() and android_archive.exists(), "Missing source/build recipe"
assert not Path(".github/workflows/android.yml").exists(), (
    "An active Android build workflow must not exist; Android is source-only")
assert Path("neftyanik_v1.24.1_stable_hotfix.zip").exists(), "Shared Flutter base is missing"
web=web_file.read_text(encoding="utf-8")
android=android_archive.read_text(encoding="utf-8")

def recipe(source: str):
    # Shared source-building scripts, invoked in the same order as release.
    loops = re.findall(
        r'for s in ([^;\n]+);do python3 "\$GITHUB_WORKSPACE/tools/\$s";done',
        source,
    )
    assert len(loops)==1, "Expected exactly one common source loop"
    common_loop=loops[0].split()
    preparations=re.findall(
        r'python3 "\$GITHUB_WORKSPACE/tools/(prepare_promysel[^"]+\.py)"',
        source,
    )
    platform_only={
        "prepare_promysel_launcher_badge_web.py",
        "prepare_promysel_launcher_badge_android.py",
        "prepare_promysel_web_push.py",
        "prepare_promysel_cellular_startup_v201.py", # post-build Web output only; no Flutter source edits
    }
    preparations=[s for s in preparations if s not in platform_only]
    patches=re.findall(
        r'patch --batch -p1 < "\$GITHUB_WORKSPACE/tools/([^"]+\.patch)"',
        source,
    )
    checks=re.findall(
        r'python3 "\$GITHUB_WORKSPACE/tools/(test_promysel[^"]+\.py)"',
        source,
    )
    # This test checks emitted Web files and therefore has no Android equivalent.
    # Browser-only HTML output checks have no Android equivalent; the Flutter
    # source and shared sync tests must still remain byte-for-byte in parity.
    web_output_checks={"test_promysel_cellular_startup_v201.py",
                       "test_promysel_network_diagnostics_v225.py"}
    checks=[x for x in checks if x not in web_output_checks]
    return common_loop,preparations,patches,checks

web_recipe=recipe(web)
android_recipe=recipe(android)
labels=("base tools", "source patches", "patch archives", "regression gates")
for label,x,y in zip(labels,web_recipe,android_recipe):
    assert x==y, f"Web/Android source divergence in {label}:\nWeb: {x}\nAndroid: {y}"
assert "--branch=dev" in web
assert "flutter build apk" in android and "workflow_dispatch:" in android
print("PASS Web and Android share the same Flutter source patch and test chain.")
print("PASS Android recipe is archived and cannot trigger APK compilation.")
