#!/usr/bin/env python3
"""After registration fields fix: suppress double taps; refresh admin roster and reject pending requests."""
from pathlib import Path

def one(s,a,b,where):
    assert s.count(a)==1,(where,a[:90],s.count(a))
    return s.replace(a,b,1)

p=Path("lib/features/admin/admin_home_screen.dart")
s=p.read_text(encoding="utf-8")
s=one(s,"SessionService.instance.refreshWorkers().catchError((_){ });",
      "SessionService.instance.refreshWorkers(force:true).catchError((_){ });","admin init")
s=one(s,"if(v==3)unawaited(s.refreshPending().catchError((_){ }));",
      "if(v==3)unawaited(s.refreshPending().catchError((_){ }));if(v==2)unawaited(s.refreshWorkers(force:true).catchError((_){ }));","tabs")
s=one(s,"if(section==3)unawaited(s.refreshPending().catchError((_){ }));",
      "if(section==3)unawaited(s.refreshPending().catchError((_){ }));if(section==2)unawaited(s.refreshWorkers(force:true).catchError((_){ }));","dashboard navigation")
methods="""Future<void> _refreshUsersManual()async{
 try{await s.refreshWorkers(force:true);}
 catch(e){_report('Не удалось обновить персонал: '+e.toString().replaceFirst('Exception: ',''));}
}
Future<void> _rejectPending(String id,String employeeName)async{
 if(_approvingId!=null)return;
 final approved=await showDialog<bool>(context:context,builder:(d)=>AlertDialog(
   title:const Text('Не согласовать заявку?'),
   content:Text('Отклонить заявку «$employeeName»? Это не удалит сотрудников, уже согласованные заявки и производственные данные.'),
   actions:[TextButton(onPressed:()=>Navigator.pop(d,false),child:const Text('Отмена')),
     FilledButton(onPressed:()=>Navigator.pop(d,true),child:const Text('Не согласовать'))]));
 if(approved!=true||!mounted||_approvingId!=null)return;
 setState(()=>_approvingId=id);
 try{
   await s.ensureFreshToken();
   await s.rejectRemote(id);
   if(mounted)ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Заявка отклонена')));
 }catch(e){_report('Не удалось отклонить заявку: '+e.toString().replaceFirst('Exception: ',''));}
 finally{if(mounted)setState(()=>_approvingId=null);}
}
"""
s=one(s,"Future<void> _refreshPendingManual()async{",methods+"Future<void> _refreshPendingManual()async{","reject action")
b=s.index("Widget _users()=>");e=s.index("Widget _requests()=>",b)
users="""Widget _users()=>RefreshIndicator(onRefresh:_refreshUsersManual,
 child:ListView(padding:const EdgeInsets.all(12),children:[
   Row(children:[const Expanded(child:Text('Персонал',style:TextStyle(fontSize:21,fontWeight:FontWeight.w900))),
     IconButton(tooltip:'Обновить сотрудников',onPressed:_refreshUsersManual,icon:const Icon(Icons.refresh))]),
   const SizedBox(height:6),
   if(s.personnelLoading)const LinearProgressIndicator(minHeight:2),
   if(s.personnelLoadError!=null)Card(child:ListTile(
     leading:const Icon(Icons.cloud_off_outlined),title:Text(s.personnelLoadError!),
     trailing:TextButton(onPressed:_refreshUsersManual,child:const Text('Повторить')))),
   if(s.allWorkers.isEmpty&&!s.personnelLoading)const Card(child:ListTile(
     title:Text('Сотрудников пока не найдено'),subtitle:Text('Потяните вниз для обновления списка'))),
   ...s.allWorkers.map((u)=>Card(child:ListTile(
     title:Text(u.name),
     subtitle:Text('${u.role.label}${u.itrSubrole==null?'':' · ${u.itrSubrole!.label}'} · ${s.fieldName(s.userFields[u.id]??'')}'),
     trailing:PopupMenuButton<String>(tooltip:'Управление сотрудником',
       onSelected:(v){if(v=='edit')_edit(u);if(v=='delete')_deleteUser(u);},
       itemBuilder:(_)=>const [
         PopupMenuItem(value:'edit',child:Text('Редактировать сотрудника')),
         PopupMenuItem(value:'delete',child:Text('Удалить сотрудника'))]))))
 ]));
"""
s=s[:b]+users+s[e:]
b=s.index("Widget _requests()=>");e=s.index("Widget _access()=>",b)
requests="""Widget _requests()=>RefreshIndicator(onRefresh:_refreshPendingManual,
 child:ListView(padding:const EdgeInsets.all(12),children:[
   Row(children:[const Expanded(child:Text('Регистрации',style:TextStyle(fontSize:21,fontWeight:FontWeight.w900))),
     IconButton(tooltip:'Обновить заявки',onPressed:_refreshPendingManual,icon:const Icon(Icons.refresh))]),
   if(s.allPending.isEmpty)const Card(child:Padding(padding:EdgeInsets.all(18),child:Text('Заявок нет.'))),
   ...s.allPending.map((p)=>Card(child:Padding(padding:const EdgeInsets.fromLTRB(6,4,10,9),
     child:Column(crossAxisAlignment:CrossAxisAlignment.stretch,children:[
       ListTile(title:Text(p.name),subtitle:Text('${p.role.label} · ${p.fieldId.isEmpty?'Новое месторождение':s.fieldName(p.fieldId)}')),
       OverflowBar(spacing:8,overflowSpacing:8,alignment:MainAxisAlignment.end,children:[
         OutlinedButton.icon(icon:const Icon(Icons.close,size:17),
           onPressed:_approvingId==null?()=>_rejectPending(p.id,p.name):null,
           label:const Text('Не согласовать')),
         FilledButton(onPressed:_approvingId==null?()=>_approvePending(p.id):null,
           child:_approvingId==p.id?const SizedBox(width:18,height:18,child:CircularProgressIndicator(strokeWidth:2)):
             const Text('Согласовать'))
       ])
     ]))))
 ]));
"""
s=s[:b]+requests+s[e:]
assert s.count("Не согласовать")>=2
p.write_text(s,encoding="utf-8")

p=Path("lib/core/services/session_service.dart")
s=p.read_text(encoding="utf-8")
s=one(s,"await Future.wait([refreshFields(),refreshPending(),refreshWorkers()]);",
      "await Future.wait([refreshFields(),refreshPending(),refreshWorkers(force:true)]);","approval forces personnel refresh")
p.write_text(s,encoding="utf-8")

p=Path("lib/features/auth/login_screen.dart")
s=p.read_text(encoding="utf-8")
s=one(s,"child:Text(register?'Отправить заявку':'Войти')",
      "child:Text(loading?(register?'Отправка…':'Вход…'):(register?'Отправить заявку':'Войти'))","register loading indicator")
b=s.index(" Future<void> _register()async{");e=s.index(" Future<void> _forgot()",b)
registration=""" Future<void> _register()async{
   if(loading)return;
   if(name.text.trim().isEmpty){setState(()=>error='Введите ФИО');return;}
   if(fieldId!='new'&&!SessionService.instance.approvedFields.any((f)=>f.id==fieldId)){
     setState(()=>error='Сначала выберите действующее месторождение.');return;
   }
   if(fieldId=='new'&&role!=UserRole.shopChief){setState(()=>error='Выберите месторождение из списка.');return;}
   setState((){loading=true;error=null;});
   try{
     await SessionService.instance.register(name:name.text.trim(),email:email.text.trim(),role:role,
       subrole:role==UserRole.engineer?subrole:null,fieldId:fieldId,newFieldName:newField.text);
     if(!mounted)return;
     await showDialog<void>(context:context,builder:(ctx)=>AlertDialog(
       title:const Text('Заявка отправлена'),
       content:Text('Если заявка ещё не рассмотрена, ожидайте согласования. После одобрения письмо придёт на ${email.text.trim()}.'),
       actions:[TextButton(onPressed:()=>Navigator.pop(ctx),child:const Text('Понятно'))]));
     if(mounted)setState(()=>register=false);
   }catch(e){if(mounted)setState(()=>error=e.toString().replaceFirst('Exception: ',''));}
   finally{if(mounted)setState(()=>loading=false);}
 }
"""
s=s[:b]+registration+s[e:]
p.write_text(s,encoding="utf-8")
print("PASS admin registration: reject action, forced roster refresh, and double-tap prevention")
