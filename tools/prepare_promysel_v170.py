from pathlib import Path
import re
r=Path.cwd()

# v1.70: field display correctness + iPhone/PWA startup performance.
home=r/'lib/features/home/home_screen.dart'; h=home.read_text()
patterns=[
 (r"Text\(s\.currentFieldId\s*\?\?\s*'[^']*'\)","Text(s.fieldName(s.currentFieldId??''))"),
 (r'Text\(s\.currentFieldId\s*\?\?\s*"[^"]*"\)',"Text(s.fieldName(s.currentFieldId??''))"),
 (r"(final\s+(?:fieldName|fieldTitle|currentFieldName)\s*=\s*)s\.currentFieldId\s*\?\?\s*'[^']*';",r"\1s.fieldName(s.currentFieldId??'');"),
 (r'(final\s+(?:fieldName|fieldTitle|currentFieldName)\s*=\s*)s\.currentFieldId\s*\?\?\s*"[^"]*";',r"\1s.fieldName(s.currentFieldId??'');"),
]
for pat,repl in patterns:h=re.sub(pat,repl,h)
h=re.sub(r"(final\s+fieldName\s*=\s*)([^;]*currentFieldId[^;]*);",lambda m:m.group(0) if 'fieldName(' in m.group(2) else m.group(1)+"s.fieldName(s.currentFieldId??'');",h)
home.write_text(h)

sess=r/'lib/core/services/session_service.dart'; s=sess.read_text()
if '_fieldNameCache' not in s:
    pos=s.rfind('\n}')
    helper="""\n final Map<String,String> _fieldNameCache={};\n String displayFieldName(String id){final live=fields.where((f)=>f.id==id).firstOrNull?.name;final n=(live??_fieldNameCache[id]??'').trim();if(n.isNotEmpty&&!n.startsWith('field_')){_fieldNameCache[id]=n;return n;}return 'Месторождение';}\n"""
    s=s[:pos]+helper+s[pos:]
s=re.sub(r"String\s+fieldName\(String\s+id\)\s*=>[^;]+;","String fieldName(String id)=>displayFieldName(id);",s)
sess.write_text(s)

main=r/'lib/main.dart'; m=main.read_text()
m=m.replace("\n  await AppStateStore.instance.loadLocal();","")
m=m.replace("if(SessionService.instance.currentFieldId!=null){await SyncService.instance.syncNow();}","if(SessionService.instance.currentFieldId!=null){unawaited(SyncService.instance.syncNow());}")
if 'unawaited(' in m and "import 'dart:async';" not in m:m="import 'dart:async';\n"+m
main.write_text(m)

s=sess.read_text();s=s.replace("unawaited(refreshFields().catchError((_){ }));unawaited(refreshPending().catchError((_){ }));notifyListeners();return", "unawaited(refreshFields().catchError((_){ }));unawaited(refreshPending().catchError((_){ }));notifyListeners();return");sess.write_text(s)

h=home.read_text();s=sess.read_text();m=main.read_text()
checks={'home_uses_human_field_name':'fieldName(' in h or 'displayFieldName(' in h,'safe_field_fallback':"return 'Месторождение'" in s and "!n.startsWith('field_')" in s,'no_duplicate_generic_state_load':'await AppStateStore.instance.loadLocal();' not in m,'startup_sync_nonblocking':'unawaited(SyncService.instance.syncNow())' in m,'field_scoped_restore':'loadLocal(fid)' in s}
print('V170 FIELD/PWA PERFORMANCE GATES',checks,flush=True);bad=[k for k,v in checks.items() if not v];assert not bad,'v1.70 gate failed: '+', '.join(bad)
print('v1.70 human field labels + nonblocking PWA startup passed')

# Apply the current release patch chain, then the compile hotfix.
v171=(Path(__file__).with_name('prepare_promysel_v171.py')).read_text()
exec(compile(v171,'prepare_promysel_v171.py','exec'),{'__name__':'__main__','__file__':str(Path(__file__).with_name('prepare_promysel_v171.py'))})
vfix=(Path(__file__).with_name('prepare_promysel_v176_fix.py')).read_text()
exec(compile(vfix,'prepare_promysel_v176_fix.py','exec'),{'__name__':'__main__','__file__':str(Path(__file__).with_name('prepare_promysel_v176_fix.py'))})
