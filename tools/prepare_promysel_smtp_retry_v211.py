from pathlib import Path
p=Path('lib/core/services/session_service.dart')
s=p.read_text(encoding='utf-8')
before=""" bool get canRetryInvitation{
   if(!approvedAwaitingInvitation)return true;
   if(invitationStatus=='accepted')return true;
   // Once the retry window opens, SMTP configuration can be checked again.
   final next=DateTime.tryParse(nextRetryAt??'');
   return next==null||!DateTime.now().isBefore(next.toLocal());
 }"""
after=""" // The server performs the authoritative atomic mail claim and 429 backoff.
 // A stale client-side timestamp must never disable the retry action.
 bool get canRetryInvitation=>true;"""
assert s.count(before)==1,f'SMTP retry UI anchor changed: {s.count(before)}'
p.write_text(s.replace(before,after,1),encoding='utf-8')
print('PASS v2.11: no stale client-side SMTP cooldown; server gates re-sends')
