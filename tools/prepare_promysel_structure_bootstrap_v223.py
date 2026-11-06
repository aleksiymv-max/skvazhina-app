#!/usr/bin/env python3
"""v2.23: read-only structure bootstrap when old unsent domains block /sync/pull.

An employee with no cached areas/pads must see the server's field structure,
even if a separate pending edit (tasks, schedule, etc.) conflicts with a
revision. Never overwrite any nonempty local structure or deletion marker;
never advance the sync cursor until the full update is accepted.
"""
from pathlib import Path

p=Path('lib/core/services/sync_service.dart')
s=p.read_text(encoding='utf-8')
# A stale successful cursor may otherwise make the server return an empty
# delta forever even though the device never stored its first area list.
original="    final recover=_cursor=='0'||lastRepair==null||"
prefix="""    final missingKey='promysel_missing_structure_probe_v223_'+fieldId;
    final localBefore=AppStateStore.instance.snapshot(fieldId);
    final localAreasBefore=localBefore['areas'];
    final localPadsBefore=localBefore['pads'];
    final missingStructure=(localAreasBefore is! List||localAreasBefore.isEmpty)&&
      (localPadsBefore is! List||localPadsBefore.isEmpty);
    final forceMissingStructure=missingStructure&&_cursor!='0'&&
      recoveryPrefs.getBool(missingKey)!=true;
    final recover=_cursor=='0'||forceMissingStructure||lastRepair==null||"""
assert s.count(original)==1,'Recover predicate anchor changed'
s=s.replace(original,prefix,1)
# The first read-only restore probe is now completed. Do not repeat it on an
# intentionally empty field each time the user opens the app.
guard="""    if(latestState!=null&&_stateDirty){
      status='Локальные изменения ожидают отправки · обновления сервера будут загружены повторно';"""
result="""    if(forceMissingStructure){
      await recoveryPrefs.setBool(missingKey,true);
    }
    if(latestState!=null&&_stateDirty){
      status='Локальные изменения ожидают отправки · обновления сервера будут загружены повторно';"""
assert s.count(guard)==1,'Cursor safety guard changed'
s=s.replace(guard,result,1)

anchor="if(latestState!=null&&!_stateDirty){"
assert s.count(anchor)==1, 'Expected one guarded snapshot apply'
new=r"""if(latestState!=null&&_stateDirty) {
      // A stale local domain queue must not hide the entire field on a new
      // phone. Copy ONLY missing structural rows. Every other unsent local
      // value remains untouched; the server cursor does not advance.
      final snapshotField=latestState['fieldId']?.toString();
      final local=AppStateStore.instance.snapshot(fieldId);
      final localAreas=local['areas'];
      final localPads=local['pads'];
      final remoteAreas=latestState['areas'];
      final remotePads=latestState['pads'];
      final removed=local['structureDeleted'];
      var hasLocalDeletion=false;
      if(removed is Map){
        for(final value in removed.values){
          if(value is List&&value.isNotEmpty){hasLocalDeletion=true;break;}
        }
      }
      final emptyLocal=(localAreas is! List||localAreas.isEmpty)&&
        (localPads is! List||localPads.isEmpty)&&!hasLocalDeletion;
      final hasRemoteStructure=remoteAreas is List&&remoteAreas.isNotEmpty&&
        remotePads is List&&remotePads.isNotEmpty;
      if(snapshotField==fieldId&&emptyLocal&&hasRemoteStructure){
        final structureOnly=Map<String,dynamic>.from(local);
        structureOnly['areas']=remoteAreas;
        structureOnly['pads']=remotePads;
        // No local tombstones: the server deletion markers are authoritative.
        if(latestState['structureDeleted'] is Map){
          structureOnly['structureDeleted']=latestState['structureDeleted'];
        }
        final cfg=local['walkConfig'];
        final emptyCfg=cfg==null||(cfg is Map&&cfg.isEmpty);
        if(emptyCfg&&latestState['walkConfig']!=null){
          structureOnly['walkConfig']=latestState['walkConfig'];
        }
        _applyingRemote=true;
        try{
          await AppStateStore.instance.apply(structureOnly);
        }finally{
          _applyingRemote=false;
        }
        // Truly empty legacy devices can inherit a revision for a phantom
        // structure queue. If a real local edit was made in this session or
        // the configuration was modified, keep the queue and the conflict.
        if(emptyCfg&&_dirtyDomains.contains('structure')&&
            (_localDomainEdits['structure']??0)==0){
          final prefs=await SharedPreferences.getInstance();
          final key='promysel_domain_pending_v211_'+fieldId+'_structure';
          final oldMarker=prefs.getString(key);
          if(oldMarker!=null){
            // Retain the old idempotency marker for forensic recovery.
            await prefs.setString(
              'promysel_blank_structure_backup_v223_'+fieldId,oldMarker);
          }
          final versions=body['domainRevisions'];
          if(versions is Map&&versions['structure'] is num){
            await prefs.setInt(_domainVersionKey(fieldId,'structure'),
              (versions['structure'] as num).toInt());
          }
          // A blank initial local cache is not a structural mutation.
          _dirtyDomains.remove('structure');
          await prefs.setStringList(_domainDirtyKey(fieldId),
            _dirtyDomains.toList());
          await prefs.remove(key);
          if(_dirtyDomains.isEmpty){
            _stateDirty=false;
            await AppStateStore.instance.clearDirty(fieldId);
          }
        }
        status='Структура месторождения загружена; '
          'неподтверждённые изменения других разделов сохранены';
        notifyListeners();
      }
    }
    if(latestState!=null&&!_stateDirty){"""
s=s.replace(anchor,new,1)
p.write_text(s,encoding='utf-8')
about=Path('lib/features/menu/about_screen.dart')
current=about.read_text(encoding='utf-8')
assert current.count('Версия v2.22')==2, 'current release labels changed'
about.write_text(current.replace('Версия v2.22','Версия v2.23'),encoding='utf-8')
print('PASS v2.23: first-login field structure restores despite pending domain conflicts')
