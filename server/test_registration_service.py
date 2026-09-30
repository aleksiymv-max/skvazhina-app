from registration_service import RegistrationService
class Passwords:
 def generate(self): return 'Temp-123456'
class Mail:
 def __init__(self): self.sent=[]
 def flush_registration(self,x): self.sent.append(x); return True
class Repo:
 def __init__(self):
  self.fields={'f1':{'id':'f1','name':'Field','approved':True}}
  self.users=[]; self.requests=[]; self.seq=0; self.locked=None
 def field(self,x): return self.fields.get(x)
 def user_by_email(self,e): return next((u for u in self.users if u['email']==e),None)
 def pending_by_email(self,e): return next((r for r in self.requests if r['email']==e and r['status']=='pending'),None)
 def create_request(self,d):
  self.seq+=1;r={**d,'id':'r'+str(self.seq),'status':'pending','requested_role':d['role'],'field_id':d.get('fieldId')};self.requests.append(r);return r
 def approved_fields(self): return list(self.fields.values())
 def pending(self): return [r for r in self.requests if r['status']=='pending']
 def claim_request(self,i):
  r=next(r for r in self.requests if r['id']==i)
  if r['status']!='pending': raise RuntimeError('already decided')
  self.locked=r;return r
 def rollback(self): self.locked=None
 def reject(self,r,a): r['status']='rejected';r['approved_by']=a['id']
 def approve(self,r,a,role,subrole,pwd):
  if r.get('creates_new_field'):
   fid='f'+str(len(self.fields)+1);self.fields[fid]={'id':fid,'name':r['newFieldName'],'approved':True};r['field_id']=fid
  u={'id':'u'+str(len(self.users)+1),'email':r['email'],'name':r['name'],'role':role,'subrole':subrole,'field_id':r['field_id'],'approved':True,'blocked':False,'must_change_password':True}
  self.users.append(u);r['status']='approved';r['approved_by']=a['id'];return u
 def queue_mail(self,r,u,p): r['mail_queued']=True
 def commit(self): self.locked=None

repo=Repo();mail=Mail();svc=RegistrationService(repo,mail,Passwords())
admin={'id':'adm','role':'admin','approved':True,'blocked':False}
# first chief creates a new field and only admin sees it
r=svc.apply({'role':'shopChief','email':'chief1@x.ru','name':'Chief 1','newFieldName':'New Field'})
assert svc.pending(admin)==[r]
assert svc.decide(admin,r['id'],True)['mailSent']
chief1=repo.users[-1]
# second chief selects existing field; admin cannot see it, existing chief can
r2=svc.apply({'role':'shopChief','email':'chief2@x.ru','name':'Chief 2','fieldId':chief1['field_id']})
assert r2 not in svc.pending(admin) and r2 in svc.pending(chief1)
svc.decide(chief1,r2['id'],True); chief2=repo.users[-1]
# employee belongs to field and both chiefs can see before decision
e=svc.apply({'role':'operator','email':'op@x.ru','name':'Operator','fieldId':chief1['field_id']})
assert e in svc.pending(chief1) and e in svc.pending(chief2)
svc.decide(chief2,e['id'],True)
assert e not in svc.pending(chief1)
try: svc.decide(chief1,e['id'],True); raise AssertionError('double decision accepted')
except RuntimeError: pass
# duplicate identity is rejected
try: svc.apply({'role':'operator','email':'op@x.ru','name':'Again','fieldId':chief1['field_id']}); raise AssertionError('duplicate accepted')
except ValueError: pass
assert len(mail.sent)==3 and all(u['must_change_password'] for u in repo.users)
print('registration service E2E chain passed')
