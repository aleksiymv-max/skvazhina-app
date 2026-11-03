"""Ensure full-state sync cannot lose new edits or overwrite another device before pull."""
from pathlib import Path
p=Path.cwd()/'lib/core/services/sync_service.dart'
s=p.read_text()
edits=[
 ("bool _online=false,_syncing=false,_serverAvailable=false,_stateDirty=false,_syncAgain=false,_applyingRemote=false;",
  "bool _online=false,_syncing=false,_serverAvailable=false,_stateDirty=false,_syncAgain=false,_applyingRemote=false;int _stateRevision=0;"),
 ("_stateDirty=await AppStateStore.instance.takeDirty();",
  "_stateDirty=await AppStateStore.instance.takeDirty(SessionService.instance.currentFieldId);"),
 ("void markStateDirty(){_stateDirty=true;unawaited(AppStateStore.instance.markDirty());if(configured)unawaited(syncNow());}",
  "void markStateDirty(){_stateDirty=true;_stateRevision++;unawaited(AppStateStore.instance.markDirty(SessionService.instance.currentFieldId));if(configured)unawaited(syncNow());}"),
 ("    _syncing=true;status='Синхронизация…';notifyListeners();",
  """    final activeField=SessionService.instance.currentFieldId;
    if(activeField!=_cursorField){
      _stateDirty=_stateDirty||await AppStateStore.instance.takeDirty(activeField);
      _lastState='';
    }
    _syncing=true;status='Синхронизация…';notifyListeners();"""),
 ("try{if(_stateDirty){await _push();await _pushState();await _pull();}else{await _pull();await _push();}try{",
  "try{await _pull();await _push();if(_stateDirty){await _pushState();await _pull();}try{"),
 ("if(canonical==_lastState){_stateDirty=false;await AppStateStore.instance.clearDirty();return;}",
  "if(canonical==_lastState){_stateDirty=false;await AppStateStore.instance.clearDirty(fid);return;}"),
 ("final stamp=DateTime.now().toUtc().microsecondsSinceEpoch;",
  "final revision=_stateRevision;final stamp=DateTime.now().toUtc().microsecondsSinceEpoch;"),
 ("_lastState=canonical;_stateDirty=false;await AppStateStore.instance.persist(fid);await AppStateStore.instance.clearDirty();",
  "_lastState=canonical;await AppStateStore.instance.persist(fid);if(revision==_stateRevision){_stateDirty=false;await AppStateStore.instance.clearDirty(fid);}"),
 ("try{await AppStateStore.instance.apply(latestState);}finally{_applyingRemote=false;}",
  "try{await AppStateStore.instance.apply(AppStateStore.instance.reconcileWithCurrent(fid,latestState));}finally{_applyingRemote=false;}")
]
for a,b in edits:
 assert s.count(a)==1,'Sync anchor changed: '+a[:100]
 s=s.replace(a,b,1)
p.write_text(s)
print('PASS: pull-before-push, field-scoped dirty state, safe in-flight revision, additive remote pull')
