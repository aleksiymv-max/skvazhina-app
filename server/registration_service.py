"""Framework-independent registration service used by FastAPI routes.
Database adapter must provide atomic claim/approve methods; mail is queued only after commit.
"""
from registration_rules import validate_chief_application,validate_employee_application,may_decide,can_login

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
  req=self.repo.claim_request(request_id)
  if not may_decide(actor,req): self.repo.rollback(); raise PermissionError('Нет прав на обработку заявки')
  if not approve:
   self.repo.reject(req,actor); self.repo.commit(); return {'status':'rejected'}
  requested_role=req['role']
  final_role=role or requested_role
  if requested_role!='shopChief' and final_role=='shopChief': self.repo.rollback(); raise PermissionError('Повышение до начальника этой заявкой запрещено')
  password=self.passwords.generate()
  user=self.repo.approve(req,actor,final_role,subrole,password)
  self.repo.queue_mail(req,user,password)
  self.repo.commit()
  sent=self.mailer.flush_registration(req['id'])
  return {'status':'approved','mailSent':sent}
 def login(self,login,password):
  email=(login or '').strip().lower()
  user=self.repo.user_by_email(email)
  if not can_login(user) or not self.repo.verify_password(user,password):
   raise PermissionError('Неверный логин или пароль')
  token=self.repo.create_auth_token(user)
  self.repo.commit()
  return {'token':token,'user':self.repo.public_user(user),'mustChangePassword':bool(user.get('must_change_password'))}
 def change_password(self,actor,password):
  if not can_login(actor): raise PermissionError('Пользователь недоступен')
  if not actor.get('must_change_password'): raise ValueError('Первичная смена пароля уже выполнена')
  self.repo.change_password(actor,password)
  self.repo.revoke_auth_tokens(actor['id'])
  token=self.repo.create_auth_token(actor)
  self.repo.commit()
  return {'token':token,'user':self.repo.public_user(actor),'mustChangePassword':False}
