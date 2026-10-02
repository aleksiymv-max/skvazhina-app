from pathlib import Path
r=Path.cwd()
p=r/'lib/core/services/sync_service.dart'
s=p.read_text()
# Scope both push and pull to the authenticated field. Insert the local fieldId
# before replacing the old fallback expressions; otherwise the generic replace
# rewrites _pull first and leaves fieldId undefined there.
s=s.replace("final queue=await _db.pendingSyncItems();","final fieldId=SessionService.instance.currentFieldId;if(fieldId==null||fieldId.isEmpty)return;final queue=await _db.pendingSyncItems();")
s=s.replace("final res=await http.get(_uri('/v1/sync/pull',{'fieldId':SessionService.instance.currentFieldId ?? 'default'","final fieldId=SessionService.instance.currentFieldId;if(fieldId==null||fieldId.isEmpty)return;final res=await http.get(_uri('/v1/sync/pull',{'fieldId':fieldId")
s=s.replace("'fieldId':SessionService.instance.currentFieldId ?? 'default'","'fieldId':fieldId")
p.write_text(s)
p=r/'lib/features/auth/login_screen.dart'
x=p.read_text().replace("final username=TextEditingController(text:'op-001'),password=TextEditingController(text:'operator')","final username=TextEditingController(),password=TextEditingController()")
p.write_text(x)
assert "?? 'default'" not in s
assert s.count("final fieldId=SessionService.instance.currentFieldId") >= 2
assert "TextEditingController(text:'op-001')" not in x
print('v1.57b field-scoped sync and no demo login passed')
