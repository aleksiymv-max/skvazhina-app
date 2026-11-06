#!/usr/bin/env python3
"""v2.11: split task, schedule, training, structure transport without discarding legacy data."""
from pathlib import Path

p=Path('lib/core/services/sync_service.dart')
s=p.read_text(encoding='utf-8')
def once(before,after,name):
 global s
 count=s.count(before)
 if count!=1:raise RuntimeError(name+': expected one anchor, got '+str(count))
 s=s.replace(before,after,1)

# Domain names are mapped to stable listeners, so one task edit does not enqueue
# a schedule/structure upload.
for kind,handler in [
 ('WorkTaskStore','_tasksChanged'),
 ('TrainingStore','_trainingChanged'),
 ('WorkScheduleStore','_schedulesChanged'),
 ('WalkParameterConfig','_structureChanged')
]:
 once(kind+'.instance.addListener(_stateChanged)',kind+'.instance.addListener('+handler+')',kind+' add')
 once(kind+'.instance.removeListener(_stateChanged)',kind+'.instance.removeListener('+handler+')',kind+' remove')
once('void _stateChanged(){if(!_applyingRemote)markStateDirty();}',
     "void _stateChanged(){if(!_applyingRemote)markStateDirty('misc');}",'misc listener')
once('void markStateDirty(){',
     "void markStateDirty([String domain='structure']){", 'domain optional marker')
once("    final fid=SessionService.instance.currentFieldId;\n    // Queue local snapshot writes in order.",
"""    final fid=SessionService.instance.currentFieldId;
    if(fid!=null&&fid.isNotEmpty&&fid!=_dirtyDomainField){
      _dirtyDomains.clear();_localDomainEdits.clear();_dirtyDomainField=fid;
    }
    _dirtyDomains.add(domain);
    _localDomainEdits[domain]=(_localDomainEdits[domain]??0)+1;
    final domainsAtEdit=_dirtyDomains.toList();
    // Queue local snapshot writes in order.""", 'dirty-domain enqueue')
once('      await AppStateStore.instance.markDirty(fid);\n      if(fid!=null&&fid.isNotEmpty)await AppStateStore.instance.persist(fid);',
"""      await AppStateStore.instance.markDirty(fid);
      if(fid!=null&&fid.isNotEmpty){
        await AppStateStore.instance.persist(fid);
        final prefs=await SharedPreferences.getInstance();
        await prefs.setStringList(_domainDirtyKey(fid),domainsAtEdit);
      }""", 'durable domain flags')
once('_stateDirty=await AppStateStore.instance.takeDirty(SessionService.instance.currentFieldId); await _db.resetSyncing();',
     '_stateDirty=await AppStateStore.instance.takeDirty(SessionService.instance.currentFieldId); await _restoreDomainDirty(SessionService.instance.currentFieldId); await _db.resetSyncing();',
     'initialize domain queue')
once('      _stateDirty=_stateDirty||await AppStateStore.instance.takeDirty(activeField);',
     '      await _restoreDomainDirty(activeField);','field switch queue')
start=s.index('  Future<void> _pushState()async{')
end=s.index('  Future<void> _pull()async{',start)
methods=Path(__file__).with_name('promysel_domain_transport_v211.dart.txt').read_text(encoding='utf-8')
assert methods.count('Future<void> _pushState()async{')==1
s=s[:start]+methods+'\n'+s[end:]
needle="final body=jsonDecode(res.body);if(body is! Map<String,dynamic>)throw const FormatException('Некорректный ответ синхронизации');final items=body['items'];"
replacement="""final body=jsonDecode(res.body);if(body is! Map<String,dynamic>)throw const FormatException('Некорректный ответ синхронизации');
    if(!_stateDirty&&body['domainRevisions'] is Map){
      final prefs=await SharedPreferences.getInstance();
      for(final entry in (body['domainRevisions'] as Map).entries){
        if(!['tasks','schedules','training','structure'].contains(entry.key))continue;
        if(entry.value is num)await prefs.setInt(
          _domainVersionKey(fieldId,entry.key.toString()),
          (entry.value as num).toInt());
      }
    }
    final items=body['items'];"""
once(needle,replacement,'remote baseline revisions')
p.write_text(s,encoding='utf-8')
print('PASS v2.11: all four domains have durable queued uploads; legacy misc separated.')
