#!/usr/bin/env python3
"""Reduce duplicated full sync reads; keep every unacknowledged edit locally.

The initial pull delivers server changes. A second pull is useful only after
all pending app-state domains were ACKed. On a 409/403/timeout, dirty flags
remain: immediately downloading the same snapshot again wastes Supabase egress
and can make users wait while their connection is already weak.
"""
from pathlib import Path

sync=Path("lib/core/services/sync_service.dart")
s=sync.read_text(encoding="utf-8")
old="if(_stateDirty){await _pushState();await _pull();}"
new="if(_stateDirty){await _pushState();if(!_stateDirty)await _pull();}"
assert s.count(old)==1, "Cannot locate v2.14 redundant post-upload sync path"
s=s.replace(old,new,1)
assert "if(!_stateDirty)await _pull();" in s
assert "await _push();" in s
assert "await _pushState();" in s
sync.write_text(s,encoding="utf-8")
print("PASS v2.15: avoid extra server pull while local domains remain unacknowledged")
