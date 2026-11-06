#!/usr/bin/env python3
"""Regression checks for the read-only, manually triggered VPN/network diagnostic."""
from pathlib import Path
import re
import subprocess
import tempfile

# Run equally from repository root and extracted Flutter project build directory.
template = Path(__file__).resolve().with_name("promysel_network_diagnostics_v225.html")
build = Path("build/web/diagnostics.html")
assert template.is_file()
source = template.read_text(encoding="utf-8")
if build.exists():
    assert source == build.read_text(encoding="utf-8"), "Generated diagnostics differ from source"
for name in (
    "promysel-app", "Supabase Edge /health", "Supabase Auth",
    "Supabase REST API", "Supabase Storage", "Мобильный интернет",
    "Wi-Fi", "VPN", "credentials:'omit'", "cache:'no-store'",
    "referrerPolicy:'no-referrer'", "no-cors", "AbortController",
    "Скопировать отчёт", "navigator.onLine",
):
    if name == "promysel-app":
        # Site is intentionally same-origin, not hardcoded to TUQO.
        assert "url:'/index.html'" in source
    else:
        assert name in source, name
assert source.count("method:'GET'") == 5
assert source.count("method:'HEAD'") == 3
assert "method:'POST'" not in source
assert "localStorage" not in source
assert "sessionStorage" not in source
assert "service_role" not in source
assert "Authorization" not in source
assert "Bearer " not in source
assert "getUser" not in source
assert "readAsBytes" not in source
assert "location.search" not in source
assert "prompt(" not in source
assert "fetch(" in source and "credentials:'omit'" in source
script = re.search(r"<script>\s*(.*?)\s*</script>", source, re.S)
assert script, "Diagnostic JavaScript not found"
with tempfile.TemporaryDirectory() as temp:
    js = Path(temp) / "network-diagnostics.js"
    js.write_text(script.group(1), encoding="utf-8")
    subprocess.run(["node", "--check", str(js)], check=True)
print("PASS v2.25: read-only no-credentials probes, no VPN claim, no private data, valid JavaScript")
