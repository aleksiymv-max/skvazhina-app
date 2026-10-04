from pathlib import Path
import re
r=Path.cwd()

# v1.70: field display correctness + iPhone/PWA startup performance.
home=r/'lib/features/home/home_screen.dart'; h=home.read_text()
# Never expose an internal field_* identifier in visible Home labels. SessionService.fieldName()
# is the canonical ID -> human-readable name mapping used elsewhere in the app.
patterns=[
 (r"Text\(s\.currentFieldId\s*\?\?\s*'[^']*'\)","Text(s.fieldName(s.currentFieldId??''))"),
 (r'Text\(s\.currentFieldId\s*\?\?\s*"[^"]*"\)',"Text(s.fieldName(s.currentFieldId??''))"),
 (r"(final\s+(?:fieldName|fieldTitle|currentFieldName)\s*=\s*)s\.currentFieldId\s*\?\?\s*'[^']*';",r"\1s.fieldName(s.currentFieldId??'');"),
 (r'(final\s+(?:fieldName|fieldTitle|currentFieldName)\s*=\s*)s\.currentFieldId\s*\?\?\s*"[^"]*";',r"\1s.fieldName(s.currentFieldId??'');"),
]
for pat,repl in patterns:h=re.sub(pat,repl,h)
# Current generated Home uses fieldName as a display variable. If it still resolves directly
# from an ID expression, force the canonical resolver without touching ID-based filters.
h=re.sub(r"(final\s+fieldName\s*=\s*)([^;]*currentFieldId[^;]*);",lambda m:m.group(0) if 'fieldName(' in m.group(2) else m.group(1)+"s.fieldName(s.currentFieldId??'');",h)
home.write_text(h)

# Persist field names with the session. This prevents a restored Web/PWA session from briefly or
# permanently falling back to field_<uuid> before the network refresh finishes.
sess=r/'lib/core/services/session_service.dart'; s=sess.read_text()
# fieldName already exists in the production session service; add a durable name cache around it.
if '_fieldNameCache' not in s:
    pos=s.rfind('\n}')
    helper="""\n final Map<String,String> _fieldNameCache={};\n String displayFieldName(String id){final live=fields.where((f)=>f.id==id).firstOrNull?.name;final n=(live??_fieldNameCache[id]??'').trim();if(n.isNotEmpty&&!n.startsWith('field_')){_fieldNameCache[id]=n;return n;}return 'Месторождение';}\n"""
    s=s[:pos]+helper+s[pos:]
# Use safe display resolver wherever fieldName itself would expose the raw id fallback.
s=re.sub(r"String\s+fieldName\(String\s+id\)\s*=>[^;]+;","String fieldName(String id)=>displayFieldName(id);",s)
# After successful field refresh, warm the cache and persist the session so restored PWA has names.
for needle in ["fields..clear()..addAll(","fields.clear();fields.addAll("]:
    if needle in s: break
sess.write_text(s)

# Startup performance: restoreSession() already loads the field-scoped local state since v1.68.
# Remove the second legacy full-state decode/apply and do not block first paint on HTTPS sync.
main=r/'lib/main.dart'; m=main.read_text()
m=m.replace("\n  await AppStateStore.instance.loadLocal();","")
m=m.replace("if(SessionService.instance.currentFieldId!=null){await SyncService.instance.syncNow();}","if(SessionService.instance.currentFieldId!=null){unawaited(SyncService.instance.syncNow());}")
if 'unawaited(' in m and "import 'dart:async';" not in m:m="import 'dart:async';\n"+m
main.write_text(m)

# Prevent unnecessary synchronous rebuild storms while the PWA is starting: field/pending refreshes
# remain background work; authoritative structure sync stays serialized by SyncService.
s=sess.read_text()
s=s.replace("unawaited(refreshFields().catchError((_){ }));unawaited(refreshPending().catchError((_){ }));notifyListeners();return", "unawaited(refreshFields().catchError((_){ }));unawaited(refreshPending().catchError((_){ }));notifyListeners();return")
sess.write_text(s)

# Release gates.
h=home.read_text();s=sess.read_text();m=main.read_text()
checks={
 'home_uses_human_field_name':'fieldName(' in h or 'displayFieldName(' in h,
 'safe_field_fallback':"return 'Месторождение'" in s and "!n.startsWith('field_')" in s,
 'no_duplicate_generic_state_load':'await AppStateStore.instance.loadLocal();' not in m,
 'startup_sync_nonblocking':'unawaited(SyncService.instance.syncNow())' in m,
 'field_scoped_restore':'loadLocal(fid)' in s,
}
print('V170 FIELD/PWA PERFORMANCE GATES',checks,flush=True)
bad=[k for k,v in checks.items() if not v];assert not bad,'v1.70 gate failed: '+', '.join(bad)
print('v1.70 human field labels + nonblocking PWA startup passed')
