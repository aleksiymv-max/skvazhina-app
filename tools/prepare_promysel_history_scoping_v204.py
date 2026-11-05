#!/usr/bin/env python3
"""v2.04: field-owned task history, server-matched local snapshots and master/operator visibility."""
from pathlib import Path

def edit(path,fn):
 p=Path(path);src=p.read_text(encoding='utf-8')
 result=fn(src);assert result!=src, 'no change: '+path
 p.write_text(result,encoding='utf-8')
def one(s,a,b,label):
 n=s.count(a)
 if n!=1:raise RuntimeError(label+': expected one match; got '+str(n)+' for '+a[:88])
 return s.replace(a,b,1)
root=Path(__file__).with_name('promysel_task_visibility_v204.dart')
assert root.is_file()
dest=Path('lib/core/services/task_visibility.dart')
assert not dest.exists()
dest.write_text(root.read_text(encoding='utf-8'),encoding='utf-8')

def model(s):
 s=one(s,
 'this.status=WorkTaskStatus.active,this.createdById,this.completedAt,this.completedBy,this.confirmedAt,this.confirmedBy});',
 'this.status=WorkTaskStatus.active,this.createdById,this.fieldId,this.completedById,this.confirmedById,this.completedAt,this.completedBy,this.confirmedAt,this.confirmedBy});',
 'task model constructor')
 s=one(s,'  final String? createdById;',
   '  final String? createdById,fieldId;\n  String? completedById,confirmedById;',
   'task owner fields')
 s=one(s,'bool complete(WorkTask t,String user,{String? comment})',
    'bool complete(WorkTask t,String user,{String? comment,String? userId})',
    'record who completed')
 s=one(s,'t.completedBy=user;t.completionComment=',
    't.completedBy=user;t.completedById=userId;t.completionComment=',
    'persist completing employee id')
 s=one(s,'t.completedAt=null;t.completedBy=null;notifyListeners();',
    't.completedAt=null;t.completedBy=null;t.completedById=null;notifyListeners();',
    'clear completion on rejection')
 s=one(s,'t.confirmedBy=userName;notifyListeners();',
    't.confirmedBy=userName;t.confirmedById=userId;notifyListeners();',
    'record reviewer id')
 return s
edit('lib/core/models/work_task.dart',model)

def completion(s):
 return one(s,'                    comment: comment.text,',
    '                    comment: comment.text,\n                    userId: SessionService.instance.currentUser.id,',
    'completion actor')
edit('lib/features/tasks/task_completion_dialog.dart',completion)

def tasks(s):
 s="import '../../core/services/task_visibility.dart';\n"+s
 s=one(s,'final active=store.tasks.where((t)=>t.status!=WorkTaskStatus.confirmed).toList();',
     'final active=store.tasks.where((t)=>t.status!=WorkTaskStatus.confirmed&&TaskVisibility.canReceive(t)).toList();',
     'active task scope')
 old='final issued=(u.role==UserRole.shopChief?store.tasks:store.tasks.where((t)=>t.createdById==u.id||(t.createdById==null&&t.createdBy==u.name))).where((t)=>t.status!=WorkTaskStatus.confirmed&&_isTaskInCurrentField(t)).toList();'
 s=one(s,old,
     'final issued=store.tasks.where((t)=>t.status!=WorkTaskStatus.confirmed&&TaskVisibility.canViewActiveIssued(t,u)).toList();',
     'master sees operator assignments even from engineers')
 start=s.index(' bool _isTaskInCurrentField(WorkTask t){')
 end=s.index(' bool _isRelevantCommon(',start)
 s=s[:start]+""" bool _isTaskInCurrentField(WorkTask t)=>
   TaskVisibility.belongsToField(t,SessionService.instance.currentFieldId);
"""+s[end:]
 a='createdById:me.id,createdAt:now'
 if s.count(a)!=2:raise RuntimeError('new task constructors count '+str(s.count(a)))
 s=s.replace(a,'createdById:me.id,fieldId:SessionService.instance.currentFieldId,createdAt:now')
 return s
edit('lib/features/tasks/tasks_screen.dart',tasks)

def snapshot(s):
 s="import 'task_visibility.dart';\n"+s
 begin=s.index('  final tasks=WorkTaskStore.instance.tasks.map(')
 end=s.index('  final ann=',begin)
 segment=s[begin:end]
 segment=one(segment,'WorkTaskStore.instance.tasks.map((t)=>',
            'WorkTaskStore.instance.tasks.where((t)=>t.fieldId==fieldId).map((t)=>',
            'snapshot accepts only owned task')
 segment=one(segment,"{'id':t.id,'title':t.title,",
             "{'id':t.id,'fieldId':fieldId,'title':t.title,",
             'serialized task field ownership')
 segment=one(segment,"'completedBy':t.completedBy,'completionComment':",
             "'completedBy':t.completedBy,'completedById':t.completedById,'completionComment':",
             'serialized completion actor')
 segment=one(segment,"'confirmedBy':t.confirmedBy,'rejectedAt':",
             "'confirmedBy':t.confirmedBy,'confirmedById':t.confirmedById,'rejectedAt':",
             'serialized reviewer actor')
 s=s[:begin]+segment+s[end:]
 # Reconcile only records with authenticated ownership. Old unscoped rows
 # may remain in disk cache for historical recovery but may not be re-uploaded.
 start=s.index("   for(final kind in ['areas','pads','tasks','annulus','training','notifications'])")
 s=s[:start]+"""   final legacyTaskRows=out['tasks'];
   if(legacyTaskRows is List){
     out['tasks']=legacyTaskRows.where((raw)=>raw is Map&&raw['fieldId']==fid).toList();
   }
"""+s[start:]
 # The late merge must never put unscoped task entries back into the snapshot.
 anchor="   out['walkConfig']=config;out['fieldId']=fid;"
 s=one(s,anchor,
     "   out['walkConfig']=config;out['fieldId']=fid;\n"
     "   out['tasks']=(out['tasks'] as List? ??const []).where((raw)=>raw is Map&&raw['fieldId']==fid).toList();",
     'enforce task scope after merge')
 start=s.index("  final tasks=(s['tasks'] as List?")
 end=s.index('  final c=s[',start)
 seg=s[start:end]
 seg=one(seg,'.whereType<Map>().map((m){',
         ".whereType<Map>().where((row)=>row['fieldId']==fid).map((m){",
         'untrusted local legacy tasks excluded')
 seg=one(seg,"createdById:x['createdById']?.toString(),",
         "createdById:x['createdById']?.toString(),fieldId:fid,completedById:x['completedById']?.toString(),confirmedById:x['confirmedById']?.toString(),",
         'parsed field and identity')
 seg=one(seg,'WorkTaskStore.instance.tasks..clear()..addAll(tasks);',
         'WorkTaskStore.instance.tasks..clear()..addAll(tasks.where(TaskVisibility.canReceive));',
         'never keep unauthorized tasks in memory')
 s=s[:start]+seg+s[end:]
 return s
edit('lib/core/services/app_state_store.dart',snapshot)

def history(s):
 s="import '../../core/services/task_visibility.dart';\n"+s
 s=one(s,'WorkTaskStore.instance.tasks.where((t)=>t.status==WorkTaskStatus.confirmed)',
    'WorkTaskStore.instance.tasks.where((t)=>t.status==WorkTaskStatus.confirmed&&TaskVisibility.canViewHistory(t))',
    'task history by role')
 s=one(s,'tasks:WorkTaskStore.instance.tasks);',
       'tasks:WorkTaskStore.instance.tasks.where(TaskVisibility.canViewHistory).toList());',
       'export restricted by same role')
 # Refresh selected field and resolved problems on account/field transition.
 s=one(s,'  Timer? _historySearchTimer;',
 """  Timer? _historySearchTimer;
  String _currentScope='';
  void _onSessionChanged(){
    if(!mounted)return;
    final session=SessionService.instance;
    final scope=session.currentUser.id+':'+(session.currentFieldId??'');
    if(scope==_currentScope)return;
    _currentScope=scope;
    setState((){
      padId=demoPads.where((p)=>p.fieldId==session.currentFieldId).firstOrNull?.id;
      _setWell();
      items.clear();_hasMore=false;
      _resolvedProblemsFuture=repo.resolvedProblems();
    });
    _load();
  }""",
  'clear history on account switch')
 s=one(s,'@override void initState(){super.initState();padId=demoPads.where((p)=>SessionService.instance.canSeeField(p.fieldId)).firstOrNull?.id;',
 """@override void initState(){
   super.initState();
   _currentScope=SessionService.instance.currentUser.id+':'+
     (SessionService.instance.currentFieldId??'');
   SessionService.instance.addListener(_onSessionChanged);
   padId=demoPads.where((p)=>p.fieldId==SessionService.instance.currentFieldId).firstOrNull?.id;""",
  'session scoped init')
 s=one(s,'@override void dispose(){WorkTaskStore.instance.removeListener(_refreshHistory);',
    '@override void dispose(){SessionService.instance.removeListener(_onSessionChanged);WorkTaskStore.instance.removeListener(_refreshHistory);',
    'prevent leaking session listener')
 s=one(s,'demoPads.where((p)=>SessionService.instance.canSeeField(p.fieldId))',
       'demoPads.where((p)=>p.fieldId==SessionService.instance.currentFieldId)',
       'history pad picker scope')
 return s
edit('lib/features/history/history_screen.dart',history)

# Active walk/task cards cannot show stale rows from a different field.
for path in ['lib/features/walk/walk_area_screen.dart',
             'lib/features/walk/pad_walk_card_screen.dart',
             'lib/features/areas/area_screen.dart']:
 def walk(s):
  s="import '../../core/services/task_visibility.dart';\n"+s
  return one(s,'WorkTaskStore.instance.tasks.where((t)=>t.status!=WorkTaskStatus.confirmed&&',
      'WorkTaskStore.instance.tasks.where((t)=>TaskVisibility.canReceive(t)&&t.status!=WorkTaskStatus.confirmed&&',
      'walking tasks in current field')
 edit(path,walk)

def session(s):
 s="import '../models/work_task.dart';\n"+s
 s=one(s,'Future<void> logout()async{await TaskLauncherBadgeService.instance.unregisterPush();await clearPersistedSession();currentUser=',
         'Future<void> logout()async{await TaskLauncherBadgeService.instance.unregisterPush();await clearPersistedSession();WorkTaskStore.instance.tasks.clear();currentUser=',
         'purge task memory on logout')
 s=one(s,'if(fid!=null&&fid.isNotEmpty)userFields[id]=fid;await _persistSession();',
       'if(fid!=null&&fid.isNotEmpty)userFields[id]=fid;WorkTaskStore.instance.tasks.clear();await _persistSession();',
       'purge task memory on new login')
 return s
edit('lib/core/services/session_service.dart',session)
print('PASS v2.04 role/field-safe task history, active tasks, exports, local sync and account switch')
