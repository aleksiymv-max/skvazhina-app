#!/usr/bin/env python3
"""v2.05: registration UI understands APPROVED/EMAIL-QUEUED independently."""
from pathlib import Path

def patch(path,old,new,label):
 p=Path(path);s=p.read_text(encoding='utf-8')
 n=s.count(old)
 if n!=1:raise RuntimeError(label+': expected one location, got '+str(n))
 p.write_text(s.replace(old,new,1),encoding='utf-8')

path='lib/core/services/session_service.dart'
patch(path,
 'required this.fieldId,this.requiresAdmin=false});',
 '''required this.fieldId,this.requiresAdmin=false,this.status='pending',
   this.invitationStatus='not_approved',this.nextRetryAt,this.attempts=0});
'''.rstrip('\n'),'PendingUser ctor')
patch(path,
 'final bool requiresAdmin; bool approved=false; String? temporaryPassword;',
 '''final bool requiresAdmin;
 final String status,invitationStatus;
 final String? nextRetryAt;
 final int attempts;
 bool get approvedAwaitingInvitation=>status=='approved_awaiting_invitation';
 bool get canRetryInvitation{
   if(!approvedAwaitingInvitation)return true;
   if(invitationStatus=='accepted')return true;
   if(invitationStatus=='action_required')return false;
   final next=DateTime.tryParse(nextRetryAt??'');
   return next==null||!DateTime.now().isBefore(next.toLocal());
 }
 String get invitationDescription{
   if(!approvedAwaitingInvitation)return 'Ожидает согласования начальником цеха';
   if(invitationStatus=='action_required')
     return 'Заявка согласована. Почтовый сервис требует настройки SMTP.';
   if(invitationStatus=='accepted')
     return 'Письмо принято почтовым сервисом. Требуется завершить подключение сотрудника.';
   final next=DateTime.tryParse(nextRetryAt??'');
   if(next!=null&&DateTime.now().isBefore(next.toLocal())){
     final time=next.toLocal();
     final hour=time.hour.toString().padLeft(2,'0');
     final minute=time.minute.toString().padLeft(2,'0');
     return 'Заявка согласована. Письмо в очереди, повторная попытка после $hour:$minute.';
   }
   return 'Заявка согласована. Письмо ожидает отправки.';
 }
 bool approved=false; String? temporaryPassword;''',
 'PendingUser status')
patch(path,
 'fieldId:fid,requiresAdmin:_role(m[\'role\'])==UserRole.shopChief));',
 '''fieldId:fid,requiresAdmin:_role(m['role'])==UserRole.shopChief,
 status:(m['status']??'pending').toString(),
 invitationStatus:(m['invitationStatus']??'not_approved').toString(),
 nextRetryAt:m['nextRetryAt']?.toString(),
 attempts:(m['attempts'] as num?)?.toInt()??0));''',
 'pending registration parse')
patch(path,
 ' await Future.wait([refreshFields(force:true),refreshPending(force:true),refreshWorkers(force:true)]);',
 ''' await refreshPending(force:true);
 if(result['invitationSent']==true){
   unawaited(refreshFields(force:true).catchError((_){ }));
   unawaited(refreshWorkers(force:true).catchError((_){ }));
 }''',
 'do not block queued invite status behind roster requests')

path='lib/features/admin/chief_approvals_screen.dart'
patch(path,
 'Future<void> _decide(String requestId,String name,bool approve)async{',
 'Future<void> _decide(String requestId,String name,bool approve,{bool alreadyApproved=false})async{',
 'separate invitation retry action')
patch(path,
 "title:Text(approve?'Согласовать сотрудника?':'Отклонить заявку?'),",
 "title:Text(approve?(alreadyApproved?'Проверить отправку приглашения?':'Согласовать сотрудника?'):'Отклонить заявку?'),",
 'chief approval confirmation')
patch(path,
 "child:Text(approve?'Согласовать':'Отклонить')),",
 "child:Text(approve?(alreadyApproved?'Повторить':'Согласовать'):'Отклонить')),",
 'confirmation action')
patch(path,
 'if(approve){await s.approveRemote(requestId);}',
 'final result=approve?await s.approveRemote(requestId):<String,dynamic>{};\n      if(!approve){await s.rejectRemote(requestId);}',
 'show actual server result')
patch(path,
 'else{await s.rejectRemote(requestId);}\n      if(!mounted)return;',
 'if(!mounted)return;',
 'remove duplicate reject')
patch(path,
 "content:Text(approve?'Заявка согласована':'Заявка отклонена')));",
 "content:Text(approve?(result['detail']??'Заявка согласована').toString():'Заявка отклонена'),duration:const Duration(seconds:7)));",
 'email status snackbar')
patch(path,
 '''              const SizedBox(height:10),
              Wrap(spacing:8,runSpacing:8,children:[
                OutlinedButton(onPressed:deciding==null?
                  ()=>_decide(p.id,p.name,false):null,child:const Text('Отклонить')),
                FilledButton(onPressed:deciding==null?
                  ()=>_decide(p.id,p.name,true):null,
                  child:deciding==p.id?const SizedBox(height:18,width:18,
                    child:CircularProgressIndicator(strokeWidth:2)):
                    const Text('Согласовать')),
              ]),''',
 '''              const SizedBox(height:6),
              Text(p.invitationDescription,
                style:TextStyle(fontSize:13,
                  color:p.approvedAwaitingInvitation?
                     Theme.of(context).colorScheme.primary:
                     Theme.of(context).colorScheme.onSurfaceVariant)),
              const SizedBox(height:10),
              Wrap(spacing:8,runSpacing:8,children:[
                if(!p.approvedAwaitingInvitation)
                  OutlinedButton(onPressed:deciding==null?
                    ()=>_decide(p.id,p.name,false):null,child:const Text('Отклонить')),
                FilledButton(onPressed:deciding==null&&p.canRetryInvitation?
                  ()=>_decide(p.id,p.name,true,
                    alreadyApproved:p.approvedAwaitingInvitation):null,
                  child:deciding==p.id?const SizedBox(height:18,width:18,
                    child:CircularProgressIndicator(strokeWidth:2)):
                    Text(p.approvedAwaitingInvitation?'Повторить приглашение':'Согласовать')),
              ]),''',
 'approved but mail queued never shown as rejectable')

path='lib/features/admin/admin_home_screen.dart'
patch(path,
 "ListTile(title:Text(p.name),subtitle:Text('${p.role.label} · ${p.fieldId.isEmpty?'Новое месторождение':s.fieldName(p.fieldId)}')),",
 "ListTile(title:Text(p.name),subtitle:Text('${p.role.label} · ${p.fieldId.isEmpty?'Новое месторождение':s.fieldName(p.fieldId)}\\n${p.invitationDescription}')),",
 'admin queue state appears')
patch(path,
 """         OutlinedButton.icon(icon:const Icon(Icons.close,size:17),
           onPressed:_approvingId==null?()=>_rejectPending(p.id,p.name):null,
           label:const Text('Не согласовать')),
         FilledButton(onPressed:_approvingId==null?()=>_approvePending(p.id):null,
           child:_approvingId==p.id?const SizedBox(width:18,height:18,child:CircularProgressIndicator(strokeWidth:2)):
             const Text('Согласовать'))""",
 """         if(!p.approvedAwaitingInvitation)
           OutlinedButton.icon(icon:const Icon(Icons.close,size:17),
             onPressed:_approvingId==null?()=>_rejectPending(p.id,p.name):null,
             label:const Text('Не согласовать')),
         FilledButton(onPressed:_approvingId==null&&p.canRetryInvitation?
           ()=>_approvePending(p.id):null,
           child:_approvingId==p.id?const SizedBox(width:18,height:18,
             child:CircularProgressIndicator(strokeWidth:2)):
             Text(p.approvedAwaitingInvitation?'Повторить приглашение':'Согласовать'))""",
 'admin buttons respect approved queue states')
print('PASS v2.05: chief/admin display approved awaiting mail, safe retry times and response detail')
