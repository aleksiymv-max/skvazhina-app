#!/usr/bin/env python3
"""Request/ownership audit v1.92. Shared Web and Android source patch."""
from pathlib import Path

def sub(path,old,new,label):
 p=Path(path);s=p.read_text(encoding='utf-8');count=s.count(old)
 if count!=1:raise AssertionError(f'{label} expected once, found {count}')
 p.write_text(s.replace(old,new,1),encoding='utf-8')

S='lib/core/services/session_service.dart'
sub(S,' Future<void> refreshFields()async{',""" Future<void>? _fieldsFlight;
 DateTime? _fieldsTime;
 Future<void> refreshFields({bool force=false})async{
   final prior=_fieldsFlight;
   if(prior!=null){try{await prior;}catch(_){if(!force)rethrow;}if(!force)return;}
   if(!force&&_fieldsTime!=null&&DateTime.now().difference(_fieldsTime!)<const Duration(minutes:2))return;
   final op=_fetchFieldsFromServer();_fieldsFlight=op;
   try{await op;}finally{if(identical(_fieldsFlight,op))_fieldsFlight=null;}
 }
 Future<void> _fetchFieldsFromServer()async{""",'field singleflight')
sub(S,'   notifyListeners();\n }\n Future<void> restoreFieldNames()async{',
      '   _fieldsTime=DateTime.now();notifyListeners();\n }\n Future<void> restoreFieldNames()async{','fields clock')
sub(S,' Future<void> refreshPending()async{final tok=api.token;if(tok==null)return;', """ Future<void>? _pendingFlight;
 DateTime? _pendingTime;
 String _pendingOwner='';
 Future<void> refreshPending({bool force=false})async{
   if(currentUser.role!=UserRole.admin&&currentUser.role!=UserRole.shopChief){
     if(pendingUsers.isNotEmpty){pendingUsers.clear();notifyListeners();}
     _pendingOwner='';_pendingTime=null;return;
   }
   final owner='${currentUser.id}:${currentFieldId??'all'}';
   final ownerChanged=owner!=_pendingOwner;
   if(ownerChanged){_pendingOwner=owner;_pendingTime=null;pendingUsers.clear();}
   final prior=_pendingFlight;
   if(prior!=null){try{await prior;}catch(_){if(!force&&!ownerChanged)rethrow;}if(!force&&!ownerChanged)return;}
   if(!force&&_pendingTime!=null&&DateTime.now().difference(_pendingTime!)<const Duration(seconds:20))return;
   final op=_fetchPendingFromServer(owner);_pendingFlight=op;
   try{await op;}finally{if(identical(_pendingFlight,op))_pendingFlight=null;}
 }
 Future<void> _fetchPendingFromServer(String owner)async{
   await ensureFreshToken();final tok=api.token;
   if(tok==null||tok.isEmpty||tok.startsWith('offline-'))return;""",'pending role gate')
sub(S,"final raw=d['items'];pendingUsers.clear();if(raw is List)","final raw=d['items'];if(owner!=_pendingOwner||owner!='${currentUser.id}:${currentFieldId??'all'}'||(currentUser.role!=UserRole.admin&&currentUser.role!=UserRole.shopChief))return;pendingUsers.clear();_pendingTime=DateTime.now();if(raw is List)",'pending owner scope')
sub(S,"unawaited(refreshFields().catchError((_){ }));unawaited(refreshPending().catchError((_){ }));notifyListeners();return d['mustChangePassword']==true;",
      "unawaited(refreshFields().catchError((_){ }));if(currentUser.role==UserRole.admin||currentUser.role==UserRole.shopChief)unawaited(refreshPending().catchError((_){ }));notifyListeners();return d['mustChangePassword']==true;",'login role-scope')
for old,new,label in [
 ('await Future.wait([refreshFields(),refreshPending(),refreshWorkers(force:true)])','await Future.wait([refreshFields(force:true),refreshPending(force:true),refreshWorkers(force:true)])','approval fresh'),
 ('await RegistrationService.instance.reject(tok,id);await refreshPending();','await RegistrationService.instance.reject(tok,id);await refreshPending(force:true);','reject fresh'),
 ('await RegistrationService.instance.adminAddField(_adminToken(),name.trim());await refreshFields();','await RegistrationService.instance.adminAddField(_adminToken(),name.trim());await refreshFields(force:true);','field added'),
 ('await RegistrationService.instance.adminRenameField(_adminToken(),id,name.trim());await refreshFields();','await RegistrationService.instance.adminRenameField(_adminToken(),id,name.trim());await refreshFields(force:true);','field renamed'),
 ('await RegistrationService.instance.adminDeleteField(_adminToken(),id,exactName);await refreshFields();','await RegistrationService.instance.adminDeleteField(_adminToken(),id,exactName);await refreshFields(force:true);','field deleted'),
 ("currentUser=const AppUser(id:'',name:'',role:UserRole.operator,approved:false);notifyListeners();}","currentUser=const AppUser(id:'',name:'',role:UserRole.operator,approved:false);pendingUsers.clear();_pendingOwner='';_pendingTime=null;notifyListeners();}",'logout clears approvals'),
]:sub(S,old,new,label)
L='lib/features/auth/login_screen.dart'
sub(L,'   SessionService.instance.addListener(_onFieldsUpdated);\n   _fetchFields();','   SessionService.instance.addListener(_onFieldsUpdated);\n   // Registration-only data: do not fetch on the ordinary login form.','login request isolation')
sub(L,'await SessionService.instance.refreshFields().timeout','await SessionService.instance.refreshFields(force:true).timeout','registration forced fresh')
sub(L,"TextButton(onPressed:()=>setState(()=>register=!register),child:Text(register?'Вернуться ко входу':'Регистрация сотрудника'))",
      "TextButton(onPressed:(){final opening=!register;setState(()=>register=!register);if(opening)unawaited(_fetchFields());},child:Text(register?'Вернуться ко входу':'Регистрация сотрудника'))",'tab-driven fields')
sub(L,"   setState((){\n     if(!_fieldManuallyChosen&&options.isNotEmpty&&\n        !options.any((f)=>f.id==fieldId)){\n       fieldId=options.first.id;\n     }\n   });",
      "   if(!_fieldManuallyChosen&&options.isNotEmpty&&!options.any((f)=>f.id==fieldId))setState(()=>fieldId=options.first.id);",'avoid unrelated login repaint')
for path in ['lib/features/home/home_screen.dart','lib/features/organization/profile_screen.dart','lib/features/organization/personnel_screen.dart']:
 sub(path,'SessionService.instance.refreshPresence(force:true).catchError((_){ })',
    'SessionService.instance.refreshPresence().catchError((_){ })','reuse presence across screens')
sub('lib/features/admin/admin_home_screen.dart','try{await s.refreshPending();}','try{await s.refreshPending(force:true);}','admin explicit reload')
T='lib/core/services/sync_service.dart'
sub(T,'  Future<void> _localSave=Future<void>.value();','  Future<void> _localSave=Future<void>.value();\n  bool _sourceListenersBound=false;','listener guard')
sub(T,'await _refreshCount();WorkTaskStore.instance.addListener(_stateChanged);','await _refreshCount();if(!_sourceListenersBound){_sourceListenersBound=true;WorkTaskStore.instance.addListener(_stateChanged);','listener guard start')
sub(T,'WorkScheduleStore.instance.addListener(_stateChanged); if(_online&&configured)','WorkScheduleStore.instance.addListener(_stateChanged);} if(_online&&configured)','listener guard end')
sub(T,'Timer.periodic(const Duration(seconds:90)','Timer.periodic(const Duration(seconds:150)','idle polling')
sub(T,'TrainingStore.instance.removeListener(_stateChanged);super.dispose();','TrainingStore.instance.removeListener(_stateChanged);WorkScheduleStore.instance.removeListener(_stateChanged);super.dispose();','schedule listener cleanup')
B='lib/core/services/task_launcher_badge.dart'
sub(B,'  DateTime? _lastDeliveredSyncAt;','  DateTime? _lastDeliveredSyncAt;\n  DateTime? _lastDeliveryAt;String? _lastDeliveryIdentity;','push cooldown state')
sub(B,'    _lastDeliveredSyncAt=at;\n    unawaited(_deliver(session.token!,fieldId));', """    // A routine data sync is not an event in the push queue.
    final identity='${session.currentUser.id}:$fieldId',now=DateTime.now();
    if(_lastDeliveryIdentity==identity&&_lastDeliveryAt!=null&&
        now.difference(_lastDeliveryAt!)<const Duration(minutes:3))return;
    _lastDeliveredSyncAt=at;_lastDeliveryAt=now;_lastDeliveryIdentity=identity;
    unawaited(_deliver(session.token!,fieldId));""",'push not coupled to each sync')
print('PASS v1.92 request routing source patch')
