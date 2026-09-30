from registration_rules import *
admin={'id':'adm','role':'admin','approved':True}
chief={'id':'c1','role':'shopChief','field_id':'f1','approved':True}
other={'id':'c2','role':'shopChief','field_id':'f2','approved':True}
rchief={'id':'r1','requested_role':'shopChief','status':'pending'}
remp={'id':'r2','requested_role':'operator','status':'pending','chief_id':'c1','field_id':'f1'}
assert may_decide(admin,rchief)
assert not may_decide(chief,rchief)
assert may_decide(chief,remp)
assert not may_decide(other,remp)
assert not may_decide(admin,remp)
assert validate_employee_application({'role':'operator','chiefId':'c1','fieldId':'f1'},chief)
for role in ('admin','shopChief'):
 try: validate_employee_application({'role':role,'chiefId':'c1','fieldId':'f1'},chief); raise AssertionError(role)
 except ValueError: pass
assert public_field({'id':'f1','approved':True,'chief_user_id':'c1'},chief)
assert not public_field({'id':'f1','approved':False,'chief_user_id':'c1'},chief)
assert can_login(chief)
assert not can_login({'approved':False,'blocked':False})
assert not can_login({'approved':True,'blocked':True})
print('registration domain E2E role gates passed')
