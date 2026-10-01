"""SMTP delivery. Credentials are read only from server environment."""
import os,smtplib
from email.message import EmailMessage
from email.utils import formatdate,make_msgid

class SmtpMailer:
 def __init__(self,repo): self.repo=repo
 def flush_registration(self,registration_id):
  item=self.repo.mail_for_registration(registration_id)
  if not item:return False
  host=os.getenv('SMTP_HOST',''); user=os.getenv('SMTP_USERNAME',''); pwd=os.getenv('SMTP_PASSWORD',''); sender=os.getenv('SMTP_FROM','')
  if not host or not sender:
   self.repo.mail_failed(item['id'],'SMTP is not configured');return False
  msg=EmailMessage();msg['Subject']='Промысел — регистрация подтверждена';msg['From']=sender;msg['To']=item['recipient'];msg['Date']=formatdate(localtime=False);msg['Message-ID']=make_msgid()
  msg.set_content('Ваша регистрация в приложении «Промысел» подтверждена.\n\nЛогин: '+item['recipient']+'\nВременный пароль: '+item['payload']['temporaryPassword']+'\n\nПри первом входе приложение потребует установить новый пароль.')
  try:
   port=int(os.getenv('SMTP_PORT','587'))
   with smtplib.SMTP(host,port,timeout=15) as s:
    if os.getenv('SMTP_STARTTLS','1')=='1':s.starttls()
    if user:s.login(user,pwd)
    s.send_message(msg)
   self.repo.mail_sent(item['id']);return True
  except Exception as e:
   self.repo.mail_failed(item['id'],str(e)[:500]);return False
