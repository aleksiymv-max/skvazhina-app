-- v2.06: immutable avatar delete/set intent, with server revision guard.
-- Legacy app_state is a shared snapshot, not authoritative for avatar deletion.
-- An old device cannot re-create a deleted image by sending a stale snapshot.
begin;
create table if not exists public.promysel_avatar_versions (
  field_id text not null references public.oil_fields(id) on delete restrict,
  user_id uuid not null,
  avatar_value text not null default '__deleted__',
  revision bigint not null default 1 check(revision>0),
  last_mutation_id text not null default 'legacy-delete',
  updated_at timestamptz not null default now(),
  primary key(field_id,user_id),
  constraint promysel_avatar_value_size check(length(avatar_value)<=320000),
  constraint promysel_avatar_mutation_size check(length(last_mutation_id)<=120)
);
create index if not exists promysel_avatar_versions_field
  on public.promysel_avatar_versions(field_id);
alter table public.promysel_avatar_versions enable row level security;
revoke all on public.promysel_avatar_versions from public,anon,authenticated;
grant select,insert,update on public.promysel_avatar_versions to service_role;

-- Only backfill explicit deletions issued by the photo owner.  A new
-- upload from a stale device with the very same binary is not a deliberate
-- replacement and does not cancel a previous deletion.
with deleted as (
 select distinct on(e.field_id,e.actor_id)
   e.field_id,e.actor_id,e.sequence
 from public.sync_events e
 where e.event_type='app_state'
   and e.actor_id is not null
   and e.payload->'avatars'->>(e.actor_id::text)='__deleted__'
 order by e.field_id,e.actor_id,e.sequence desc
), intentional_new_photo as (
 select distinct d.field_id,d.actor_id
 from deleted d
 join public.sync_events e on e.field_id=d.field_id
   and e.actor_id=d.actor_id and e.event_type='app_state'
   and e.sequence>d.sequence
 where e.payload->'avatars'->>(d.actor_id::text) is not null
   and e.payload->'avatars'->>(d.actor_id::text)<>'__deleted__'
   and md5(e.payload->'avatars'->>(d.actor_id::text))
     is distinct from (
       select md5(prev.payload->'avatars'->>(d.actor_id::text))
       from public.sync_events prev
       where prev.field_id=d.field_id and prev.actor_id=d.actor_id
         and prev.event_type='app_state' and prev.sequence<d.sequence
         and prev.payload->'avatars'->>(d.actor_id::text) not in('', '__deleted__')
       order by prev.sequence desc limit 1
     )
)
insert into public.promysel_avatar_versions(field_id,user_id,avatar_value,revision,last_mutation_id)
select d.field_id,d.actor_id,'__deleted__',1,'backfill-deleted-avatar'
from deleted d where not exists(
 select 1 from intentional_new_photo p
 where p.field_id=d.field_id and p.actor_id=d.actor_id)
on conflict(field_id,user_id) do nothing;

create or replace function app_private.promysel_avatar_intent_v206()
returns trigger language plpgsql security definer set search_path='' as $fn$
declare
  v_edit jsonb;
  v_id text;
  v_kind text;
  v_expect bigint;
  v_avatar text;
  v_prev bigint;
  v_operation text;
begin
  if new.event_type<>'app_state' or new.actor_id is null then return new;end if;
  v_id:=new.actor_id::text;
  v_edit:=new.payload->'avatarMutation';

  if jsonb_typeof(v_edit)='object'
     and v_edit->>'userId'=v_id
     and v_edit->>'fieldId'=new.field_id
     and v_edit->>'operationId' ~ '^[a-zA-Z0-9:_-]{8,120}$'
     and v_edit->>'expectedRevision' ~ '^[0-9]{1,14}$'
  then
    v_kind:=v_edit->>'kind';
    v_operation:=v_edit->>'operationId';
    v_expect:=(v_edit->>'expectedRevision')::bigint;
    v_avatar:=new.payload->'avatars'->>v_id;
    if v_kind='delete' then
      if v_avatar<>'__deleted__' then return new;end if;
    elsif v_kind='set' then
      if v_avatar is null or length(v_avatar)<24
         or length(v_avatar)>320000 or
         v_avatar !~ '^[A-Za-z0-9+/=]+$' then return new;end if;
    else
      return new;
    end if;

    -- Compare-and-swap in one statement; stale state snapshots may never
    -- restore a value once a newer deletion has been committed.
    insert into public.promysel_avatar_versions(
      field_id,user_id,avatar_value,revision,last_mutation_id)
    select new.field_id,new.actor_id,v_avatar,1,v_operation where v_expect=0
    on conflict(field_id,user_id) do update
      set avatar_value=excluded.avatar_value,
          revision=public.promysel_avatar_versions.revision+1,
          last_mutation_id=excluded.last_mutation_id,
          updated_at=now()
      where public.promysel_avatar_versions.revision=v_expect
        and public.promysel_avatar_versions.last_mutation_id<>v_operation;
    return new;
  end if;

  -- Backward compatibility: a legacy explicit removal can create a durable
  -- tombstone, but an older client cannot override an existing authoritative
  -- photo status (whether deleted or intentionally re-uploaded).
  if new.payload->'avatars'->>v_id='__deleted__' then
    insert into public.promysel_avatar_versions(
      field_id,user_id,avatar_value,revision,last_mutation_id)
    values(new.field_id,new.actor_id,'__deleted__',1,'legacy-delete')
    on conflict(field_id,user_id) do nothing;
  end if;
  return new;
exception when others then
  raise warning 'promysel avatar intent skipped SQLSTATE %',sqlstate;
  return new;
end $fn$;

drop trigger if exists zz_promysel_avatar_intent_v206 on public.sync_events;
create trigger zz_promysel_avatar_intent_v206
after insert on public.sync_events
for each row when(new.event_type='app_state')
execute function app_private.promysel_avatar_intent_v206();
commit;
