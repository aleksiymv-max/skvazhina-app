from registration_rules import *
admin={'id':'adm','role':'admin','approved':True,'blocked':False}
chief1={'id':'c1','role':'shopChief','field_id':'f1','approved':True,'blocked':False}
chief2={'id':'c2','role':'shopChief','field_id':'f1','approved':True,'blocked':False}
other={'id':'c3','role':'shopChief','field_id':'f2','approved':True,'blocked':False}
field={'id':'f1','approved':True}

first_chief={'requested_role':'shopChief','status':'pending','field_id':None,'creates_new_field':True}
next_chief={'requested_role':'shopChief','status':'pending','field_id':'f1','creates_new_field':False}
employee={'requested_role':'operator','status':'pending','field_id':'f1'}

# First chief/new field -> administrator only.
assert may_decide(admin,first_chief)
assert not may_decide(chief1,first_chief)

# Further chief/existing field -> any active chief of that field, never admin.
assert may_decide(chief1,next_chief) and may_decide(chief2,next_chief)
assert not may_decide(admin,next_chief) and not may_decide(other,next_chief)

# Employees follow the same field-wide chief queue.
assert may_decide(chief1,employee) and may_decide(chief2,employee)
assert not may_decide(admin,employee) and not may_decide(other,employee)

assert validate_employee_application({'role':'operator','fieldId':'f1'},field)
assert public_field(field)
assert can_login(chief1)
assert not can_login({**chief1,'blocked':True})
print('first-chief admin + existing-field multi-chief gates passed')
