-- v2.06.1: versioned avatar commit path for all approved users, including operators.
-- The shared app_state upload remains role-gated; photo changes use a separate
-- authenticated endpoint and are safe across devices and offline retries.
begin;
create or replace function public.promysel_avatar_commit_v206(
 p_field_id text,p_user_id uuid,p_avatar text,
 p_expected_revision bigint,p_operation_id text
) returns jsonb language plpgsql security definer set search_path='' as $fn$
declare existing public.promysel_avatar_versions%rowtype;
 v_rev bigint;
begin
 if p_field_id is null or p_user_id is null or
    length(p_operation_id) not between 8 and 120 or
    p_operation_id !~ '^[A-Za-z0-9:_-]+$' or
    p_expected_revision is null or p_expected_revision<0 then
   raise exception 'Некорректные параметры изменения фотографии';
 end if;
 if not exists (
   select 1 from public.field_memberships m
   where m.field_id=p_field_id and m.user_id=p_user_id
     and m.approved and not m.blocked
 ) then raise exception 'Нет допуска сотрудника к месторождению';end if;
 if p_avatar is null then p_avatar:='__deleted__';end if;
 if p_avatar<>'__deleted__' and
   (length(p_avatar) not between 24 and 320000 or
    p_avatar !~ '^[A-Za-z0-9+/=]+$')
 then raise exception 'Некорректное изображение';end if;
 select * into existing from public.promysel_avatar_versions v
   where v.field_id=p_field_id and v.user_id=p_user_id for update;
 if found then
   if existing.last_mutation_id=p_operation_id then
     return jsonb_build_object('status','already_applied','revision',existing.revision);
   end if;
   if existing.revision<>p_expected_revision then
     return jsonb_build_object('status','conflict','revision',existing.revision);
   end if;
   update public.promysel_avatar_versions
   set avatar_value=p_avatar,revision=existing.revision+1,
     last_mutation_id=p_operation_id,updated_at=now()
   where field_id=p_field_id and user_id=p_user_id
   returning revision into v_rev;
 else
   if p_expected_revision<>0 then
     return jsonb_build_object('status','conflict','revision',0);
   end if;
   insert into public.promysel_avatar_versions(
     field_id,user_id,avatar_value,revision,last_mutation_id)
   values(p_field_id,p_user_id,p_avatar,1,p_operation_id)
   returning revision into v_rev;
 end if;
 return jsonb_build_object('status','ok','revision',v_rev);
end $fn$;
revoke all on function public.promysel_avatar_commit_v206(text,uuid,text,bigint,text)
 from public,anon,authenticated;
grant execute on function public.promysel_avatar_commit_v206(text,uuid,text,bigint,text)
 to service_role;

-- Allow a tiny server-side 'avatar_change' marker to wake incremental pull
-- on older devices, without another heavyweight app_state payload.
alter table public.sync_events
  drop constraint if exists sync_events_event_type_check;
alter table public.sync_events
  add constraint sync_events_event_type_check
  check(event_type=any(array[
    'measurement','app_state','task','problem','annulus_pressure',
    'training','notification','equipment','repair','avatar_change'
  ])) not valid;
alter table public.sync_events
  validate constraint sync_events_event_type_check;

create or replace function app_private.promysel_notify_avatar_revision_v206()
returns trigger language plpgsql security definer set search_path='' as $fn$
begin
 insert into public.sync_events(event_key,field_id,device_id,event_type,
   payload,actor_id,client_updated_at)
 values('avatar-v206:'||new.field_id||':'||new.user_id::text||':'||new.revision::text,
   new.field_id,'server-avatar','avatar_change',
   jsonb_build_object('userId',new.user_id::text,
      'revision',new.revision,'deleted',new.avatar_value='__deleted__'),
   new.user_id,now())
 on conflict(event_key) do nothing;
 return new;
end $fn$;
drop trigger if exists promysel_avatar_revision_notify_v206
  on public.promysel_avatar_versions;
create trigger promysel_avatar_revision_notify_v206
after insert or update on public.promysel_avatar_versions
for each row execute function app_private.promysel_notify_avatar_revision_v206();

-- Backfilled deletions need a one-time lightweight marker to force existing
-- devices with incremental sync cursors to retrieve the repaired avatar.
insert into public.sync_events(event_key,field_id,device_id,event_type,
  payload,actor_id,client_updated_at)
select 'avatar-v206:'||a.field_id||':'||a.user_id::text||':'||a.revision::text,
 a.field_id,'server-avatar','avatar_change',
 jsonb_build_object('userId',a.user_id::text,
   'revision',a.revision,'deleted',a.avatar_value='__deleted__'),
 a.user_id,now()
from public.promysel_avatar_versions a
on conflict(event_key) do nothing;
commit;
