#!/usr/bin/env python3
"""v2.06: avatar deletion is a scoped offline queue, not shared state overwrite."""
from pathlib import Path

def one(s,a,b,label):
    n=s.count(a)
    if n!=1:raise RuntimeError(f'{label}: expected one match, got {n}')
    return s.replace(a,b,1)

p=Path('lib/core/services/avatar_store.dart')
assert p.exists()
p.write_text(Path(__file__).with_name('promysel_avatar_store_v206.dart')
             .read_text(encoding='utf-8'),encoding='utf-8')

p=Path('lib/features/organization/profile_screen.dart')
s=p.read_text(encoding='utf-8')
s=one(s,
 'await AvatarStore.instance.remove(SessionService.instance.currentUser.id);',
 '''await AvatarStore.instance.remove(SessionService.instance.currentUser.id,
      fieldId:SessionService.instance.currentFieldId??'');''',
 'profile deletes only own avatar, with field')
s=one(s,
 '''await AvatarStore.instance.setBytes(
     SessionService.instance.currentUser.id,cropped);''',
 '''await AvatarStore.instance.setBytes(
     SessionService.instance.currentUser.id,cropped,
     fieldId:SessionService.instance.currentFieldId??'');''',
 'profile uploads only own avatar, with field')
assert s.count('SyncService.instance.markStateDirty();')==2
s=s.replace('SyncService.instance.markStateDirty();',
            'SyncService.instance.queueAvatarSync();')
p.write_text(s,encoding='utf-8')

p=Path('lib/core/services/app_state_store.dart')
s=p.read_text(encoding='utf-8')
s=one(s,'await AvatarStore.instance.apply(avatars);',
  '''await AvatarStore.instance.apply(avatars,fieldId:fid,
     revisions:s['avatarVersions'] is Map?s['avatarVersions'] as Map:null);''',
  'authoritative avatar versions applied to local cache')
p.write_text(s,encoding='utf-8')

p=Path('lib/core/services/sync_service.dart')
s=p.read_text(encoding='utf-8')
s=one(s,
 'WorkScheduleStore.instance.addListener(_stateChanged);',
 'WorkScheduleStore.instance.addListener(_stateChanged);',
 'foreground event anchors')
s=one(s,'AvatarStore.instance.addListener(_stateChanged);',
      '/* Avatars sync separately: no field-wide app_state write. */',
      'stop uploading the entire field on avatar edits')
s=one(s,'AvatarStore.instance.removeListener(_stateChanged);',
      '/* AvatarStore has no field-wide snapshot listener. */',
      'remove unused snapshot listener')
s=one(s,
 '    await _refreshCount();if(!_sourceListenersBound)',
 '    await AvatarStore.instance.ensureLoaded();await _refreshCount();if(!_sourceListenersBound)',
 'read offline avatar operations before sync starts')
s=one(s,'pending=await _db.pendingSyncCount();',
 '''pending=await _db.pendingSyncCount();
    final user=SessionService.instance.currentUser.id;
    final field=SessionService.instance.currentFieldId;
    if(user.isNotEmpty&&field!=null&&field.isNotEmpty&&
      AvatarStore.instance.pendingFor(user,field)!=null)pending++;''',
 'show avatar edits in offline pending count')
anchor='  void markStateDirty(){'
new="""  // A profile photo must never cause a broad app_state snapshot re-upload.
  void queueAvatarSync(){
    status='Фотография сохранена на устройстве · ожидает синхронизации';
    notifyListeners();
    if(_syncing){_syncAgain=true;return;}
    if(configured&&_online){
      _stateDebounce?.cancel();
      _stateDebounce=Timer(const Duration(milliseconds:600),
        ()=>unawaited(syncNow()));
    }
  }

  Future<void> _pushPendingAvatar()async{
    final session=SessionService.instance;
    final field=session.currentFieldId,userId=session.currentUser.id;
    if(field==null||field.isEmpty||userId.isEmpty)return;
    await AvatarStore.instance.ensureLoaded();
    final mutation=AvatarStore.instance.pendingFor(userId,field);
    if(mutation==null)return;
    final operation=mutation['operationId'].toString();
    final request=<String,dynamic>{
      'fieldId':field,'kind':mutation['kind'],'operationId':operation,
      'expectedRevision':mutation['expectedRevision'],
      if(mutation['kind']=='set')'avatar':mutation['value'],
    };
    final res=await _client.post(_uri('/v1/avatar/mutate'),
      headers:_authHeaders,body:jsonEncode(request))
      .timeout(const Duration(seconds:32));
    if(res.statusCode==409){
      final decoded=jsonDecode(res.body);
      final current=decoded is Map?(decoded['revision'] as num?)?.toInt()??0:0;
      await AvatarStore.instance.conflict(userId,field,operation,current);
      return; // server state will be pulled below; the other edit wins
    }
    if(res.statusCode<200||res.statusCode>=300){
      throw Exception('Сервер не принял изменение фотографии: HTTP '+res.statusCode.toString());
    }
    final response=jsonDecode(res.body);
    if(response is! Map||response['revision'] is! num)
      throw const FormatException('Сервер не подтвердил версию фотографии');
    await AvatarStore.instance.accepted(
      userId,field,operation,(response['revision'] as num).toInt());
  }

"""
s=one(s,anchor,new+anchor,'avatar queue sender and foreground trigger')
s=one(s,'    await _pull();await _push();',
      '    await _pushPendingAvatar();await _pull();await _push();',
      'send avatar safely before merging remote snapshots')
p.write_text(s,encoding='utf-8')
print('PASS v2.06: profile avatar updates have durable local offline queue, server versions, no field-wide state reupload')
