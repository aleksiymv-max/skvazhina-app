#!/usr/bin/env python3
"""v2.25: verify safe VPN comparison in the FINAL generated Flutter source."""
from pathlib import Path
s=Path('lib/features/menu/about_screen.dart').read_text(encoding='utf-8')
probe=s[s.index('  Future<void> _probeApi() async {'):s.index('  Future<void> _checkApiOnly() async {')]
checks={
 'same sync server base':"Uri.parse('$_base/v1/sync/domain/revisions')" in probe,
 'real field-bound authenticated read':"SessionService.instance.currentFieldId" in probe and
   "SessionService.instance.token" in probe and "'authorization':'Bearer $token'" in probe,
 'no full sync or network mutation':"http.get(" in probe and
   all(x not in probe for x in ["http.post(", "syncNow(", "http.put(", "http.delete(",
                              "applyRemoteMeasurement", "clearDirty", "markSynced"]),
 'bounded timeout':"Duration(seconds:12)" in probe and "Stopwatch()..start()" in probe,
 'genuine response validation':"response.statusCode==200" in probe and
   "json['revisions'] is Map" in probe,
 'diagnose timeout network http and session':
   all(x in probe for x in ["NO_SESSION","SYNC_API_TIMEOUT","SYNC_API_NETWORK",
                            "SYNC_API_INVALID_JSON","HTTP_"]),
 'store compact no-identity comparisons':
   "_vpnResults[_vpnMode]" in s and "'off'" in s and "'on'" in s and
   "Clipboard.setData(" in s,
 'shown in server check screen':
   "'API синхронизации (чтение)'" in s and
   "'Проверить только API (без отправки)'" in s and
   "'Скопировать сравнение'" in s and
   "VPN:" in s,
 'one existing full sync button retained':
   s.count("FilledButton.icon(")==1 and
   "await sync.syncNow(force:true);" in s,
 'global check also probes API':"await _probeApi();" in s[s.index('Future<void> _checkAll() async {'):],
 'no destructive troubleshooting':
   all(x not in s for x in ["deleteDatabase(", "localStorage.clear(", "clearPersistedSession("]),
 'new version':'Версия v2.25' in s,
}
for name,passed in checks.items():print(('PASS ' if passed else 'FAIL ')+name)
assert all(checks.values()),'VPN network diagnostic contract failed'
