from pathlib import Path
r=Path.cwd()
p=r/'lib/core/services/session_service.dart'
s=p.read_text()
old="'name':name,'email':email,'role':roleValue"
new="'fullName':name,'email':email,'role':roleValue"
assert old in s, 'Expected legacy registration name payload not found'
s=s.replace(old,new,1)
p.write_text(s)

s=p.read_text()
assert "'fullName':name" in s
assert "final data=<String,dynamic>{'name':name" not in s
reg=(r/'lib/core/services/registration_service.dart').read_text()
assert '/v1/registration/apply' in reg
print('v1.57f live registration fullName contract passed')
