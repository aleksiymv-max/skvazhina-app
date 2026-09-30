from registration_rules import *
admin={'id':'adm','role':'admin','approved':True,'blocked':False}
chief1={'id':'c1','role':'shopChief','field_id':'f1','approved':True,'blocked':False}
chief2={'id':'c2','role':'shopChief','field_id':'f1','approved':True,'blocked':False}
other={'id':'c3','role':'shopChief','field_id':'f2','approved':True,'blocked':False}
field={'id':'f1','approved':True}
rchief={'requested_role':'shopChief','status':'pending','field_id':'f1'}
remp={'requested_role':'operator','status':'pending','field_id':'f1'}
assert may_decide(admin,rchief)
assert not may_decide(chief1,rchief)
assert may_decide(chief1,remp) and may_decide(chief2,remp)
assert not may_decide(other,remp) and not may_decide(admin,remp)
assert validate_employee_application({'role':'operator','fieldId':'f1'},field)
for role in ('admin','shopChief'):
 try: validate_employee_application({'role':role,'fieldId':'f1'},field); raise AssertionError(role)
 except ValueError: pass
assert public_field(field)
assert not public_field({'id':'f2','approved':False})
assert can_login(chief1)
assert not can_login({**chief1,'blocked':True})
print('field-wide multi-chief registration gates passed')
