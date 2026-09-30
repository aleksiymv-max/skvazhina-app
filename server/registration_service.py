"""Framework-independent registration service used by FastAPI routes.
Database adapter must provide atomic claim/approve methods; mail is queued only after commit.
"""
from registration_rules import validate_chief_application,validate_employee_application,may_decide

class RegistrationService:
 def __init__(self,repo,mailer,passwords): self.repo,self.mailer,self.passwords=repo,mailer,passwords
 def apply(self,data):
  role=data.get('role'); field=None
  if data.get('fieldId'): field=self.repo.field(data['fieldId'])
  if role=='shopChief': validate_chief_application(data,field)
  else: validate_employee_application(data,field)
  email=(data.get('email') or '').strip().lower()
  if self.repo.user_by_email(email) or self.repo.pending_by_email(email): raise ValueError('Этот e-mail уже зарегистрирован или ожидает подтверждения')
  creates=role=='shopChief' and not data.get('fieldId')
  return self.repo.create_request({**data,'email':email,'creates_new_field':creates})
 def directory(self): return self.repo.approved_fields()
 def pending(self,actor):
  rows=self.repo.pending()
  return [r for r in rows if may_decide(actor,r)]
 def decide(self,actor,request_id,approve,role=None,subrole=None):
  # repo.claim_request MUST lock row and fail if it is no longer pending.
  req=self.repo.claim_request(request_id)
  if not may_decide(actor,req): self.repo.rollback(); raise PermissionError('Нет прав на обработку заявки')
  if not approve:
   self.repo.reject(req,actor); self.repo.commit(); return {'status':'rejected'}
  final_role=role or req['requested_role']
  if req['requested_role']!='shopChief' and final_role=='shopChief': self.repo.rollback(); raise PermissionError('Повышение до начальника этой заявкой запрещено')
  password=self.passwords.generate()
  user=self.repo.approve(req,actor,final_role,subrole,password)
  self.repo.queue_mail(req,user,password)
  self.repo.commit()
  sent=self.mailer.flush_registration(req['id'])
  return {'status':'approved','mailSent':sent}
