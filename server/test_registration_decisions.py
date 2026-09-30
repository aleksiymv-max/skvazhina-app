from registration_decisions import *
admin={'id':'adm','role':'admin','approved':True,'blocked':False}
c1={'id':'c1','role':'shopChief','field_id':'f1','approved':True,'blocked':False}
c2={'id':'c2','role':'shopChief','field_id':'f1','approved':True,'blocked':False}
other={'id':'c3','role':'shopChief','field_id':'f2','approved':True,'blocked':False}

first={'id':'r1','status':'pending','requested_role':'shopChief','creates_new_field':True,'field_id':None}
assert decide_in_memory(admin,first,'approved')['status']=='approved'
try: decide_in_memory(admin,first,'approved'); raise AssertionError('double approval accepted')
except DecisionConflict: pass

next_chief={'id':'r2','status':'pending','requested_role':'shopChief','creates_new_field':False,'field_id':'f1'}
assert decide_in_memory(c2,next_chief,'approved')['approved_by']=='c2'

employee={'id':'r3','status':'pending','requested_role':'operator','creates_new_field':False,'field_id':'f1'}
try: decide_in_memory(other,employee,'approved'); raise AssertionError('foreign chief accepted')
except DecisionForbidden: pass
assert decide_in_memory(c1,employee,'rejected')['status']=='rejected'
assert 'FOR UPDATE' in approval_transaction_sql()
print('atomic registration decision tests passed')
