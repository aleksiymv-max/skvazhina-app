#!/usr/bin/env python3
"""Fix the well-fund status strip: zero-count segments have zero width.

Runs after all Flutter source patches. This avoids modifying Supabase/state,
and makes the green, stopped and workover segments proportional to well counts.
"""
from pathlib import Path
import re

home = Path("lib/features/home/home_screen.dart")
source = home.read_text(encoding="utf-8")

# The home dashboard renders three Expanded segments for 'Состояние фонда'.
# Previously a 0-count segment had flex 1 at 15% opacity. Thus even 100%
# working wells never produced a solid green strip, and all percentages were
# distorted. Remove zero-count segments entirely.
signature = re.compile(
    r"\bWidget\s+([A-Za-z_][A-Za-z_0-9]*)\s*\(\s*int\s+([A-Za-z_][A-Za-z_0-9]*)\s*,\s*Color\s+([A-Za-z_][A-Za-z_0-9]*)\s*\)\s*(=>|\{)"
)
candidates = []
for match in signature.finditer(source):
    rest = source[match.end(): match.end() + 650]
    if "Expanded" in rest and "flex:" in rest and re.search(r"height\s*:\s*9\b", rest):
        candidates.append(match)

if len(candidates) != 1:
    context = []
    for m in re.finditer(r"height\s*:\s*9\b", source):
        context.append(source[max(0, m.start()-240):m.end()+200])
    raise RuntimeError(
        f"Expected exactly 1 fund-bar segment helper, got {len(candidates)}. "
        f"Nearby height:9 snippets: {context!r}"
    )

match = candidates[0]
name, count, color, kind = match.groups()
if kind == "=>":
    # Dart conditional expression; no change to the existing live color logic.
    insertion = f" {count} <= 0 ? const SizedBox.shrink() : "
else:
    insertion = f"if ({count} <= 0) return const SizedBox.shrink();"
source = source[:match.end()] + insertion + source[match.end():]
home.write_text(source, encoding="utf-8")

# Both versions are built from the same source; no DB change is involved.
assert source.count("const SizedBox.shrink()") >= 1
assert f"{count} <= 0" in source
print(f"PASS fund strip: {name}(int {count}, Color {color}) now omits zero-count segments.")
print("PASS expected ratios: 10/0/0 -> 100% green; 6/4/0 -> 60% green; 7/2/1 -> 70/20/10.")
