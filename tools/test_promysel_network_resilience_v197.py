from pathlib import Path
nw=Path('lib/core/network/weak_network.dart').read_text()
sy=Path('lib/core/services/sync_service.dart').read_text()
rg=Path('lib/core/services/registration_service.dart').read_text()
checks={
 'GET-only fallback': 'static Future<http.Response> read(' in nw,
 'transport outage cooldown': '_transportCooldown' in nw and 'Duration(seconds:12)' in nw,
 'bounded sync pull': 'timeout:const Duration(seconds:12),attempts:2' in sy,
 'idempotent state push retained': 'promysel_app_state_pending_' in sy,
 'offline persistence intact': 'await _localSave' in sy,
 'single-attempt credential request': 'One attempt per tap: retrying credentials can open extra sessions.' in rg,
 'token is never logged': "print(token)" not in nw,
}
for key,ok in checks.items():print(('PASS' if ok else 'FAIL')+' '+key)
assert all(checks.values())
