from pathlib import Path
s=Path('lib/core/services/sync_service.dart').read_text(encoding='utf-8')
checks={
 'separate task listener':'WorkTaskStore.instance.addListener(_tasksChanged)' in s,
 'separate schedule listener':'WorkScheduleStore.instance.addListener(_schedulesChanged)' in s,
 'separate training listener':'TrainingStore.instance.addListener(_trainingChanged)' in s,
 'separate structure listener':'WalkParameterConfig.instance.addListener(_structureChanged)' in s,
 'four isolated queues':"['tasks','schedules','training','structure','misc']" in s,
 'persistent dirty domains':'_domainDirtyKey(fid)' in s,
 'partial failure does not stop other domains':'firstDomainFailure??=error;' in s and "for(final domain in ['tasks','schedules','training','structure','misc'])" in s,
 'transaction version':"'expectedRevision':prefs.getInt(_domainVersionKey(fid,domain))??0" in s,
 'single-attempt writes':"_uri(isLegacy?'/v1/sync/push':'/v1/sync/domain/push')" in s,
 'pending mutation key':'promysel_domain_pending_v211_' in s,
 'retry cursor retained':'if(latestState!=null&&_stateDirty)' in s,
 'schedule payload only own user':"source.containsKey(mine)" in s,
 'remote baseline versions':"body['domainRevisions']" in s,
}
for name,passed in checks.items():print(('PASS ' if passed else 'FAIL ')+name)
assert all(checks.values()),'Domain transport source regression'
