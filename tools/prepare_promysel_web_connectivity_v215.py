#!/usr/bin/env python3
"""Web/iPhone PWA: navigator.onLine is only a hint, not proof of no Supabase.

Allow a bounded real HTTPS sync attempt on browser connectivity=false.
When genuinely offline, the existing HTTP timeout, exponential backoff and
durable local queue handle failure. Keep native Android signal unchanged.
"""
from pathlib import Path

p=Path("lib/core/services/sync_service.dart")
s=p.read_text(encoding="utf-8")
if "import 'package:flutter/foundation.dart';" not in s:
 s="import 'package:flutter/foundation.dart';\n"+s

old="_online=results.any((x)=>x!=ConnectivityResult.none);"
assert s.count(old)==1, "Connectivity stream anchor changed"
s=s.replace(old,"_online=kIsWeb||results.any((x)=>x!=ConnectivityResult.none);",1)

start=s.index("_subscription=Connectivity().onConnectivityChanged.listen(")
anchor="await _refreshCount();"
pos=s.find(anchor,start)
assert pos>start and pos-start<700, "Cannot find initial sync count refresh"
s=s[:pos]+"""// A PWA may report navigator.onLine=false while its API origin responds.
    // Make a bounded HTTPS attempt and let the actual result decide.
    if(kIsWeb)_online=true;
    """+s[pos:]

assert "if(kIsWeb)_online=true;" in s
assert "_online=kIsWeb||results.any(" in s
assert "if(_online&&configured)unawaited(syncNow());" in s
p.write_text(s,encoding="utf-8")
print("PASS v2.15: Web does not suppress sync solely due to navigator.onLine")
