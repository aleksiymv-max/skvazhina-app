-- v2.04: durable task-to-field ownership; no deletion of sync history.
-- Source of legacy ownership: first occurrence of the task in the immutable
-- field-scoped sync stream. Never infer ownership from today's employee roster.
begin;
create table if not exists public.promysel_task_scopes(
  task_id text primary key,
  field_id text not null references public.oil_fields(id) on delete restrict,
  first_sequence bigint,
  scope_source text not null,
  created_at timestamptz not null default now(),
  constraint promysel_task_scopes_id_size check (length(task_id) between 1 and 180)
);
alter table public.promysel_task_scopes enable row level security;
revoke all on public.promysel_task_scopes from anon,authenticated;
create index if not exists promysel_task_scopes_field_idx on public.promysel_task_scopes(field_id);

with first_seen as (
 select distinct on(t.value->>'id')
   t.value->>'id' as task_id,e.field_id,e.sequence
 from public.sync_events e
 cross join lateral jsonb_array_elements(
    case when jsonb_typeof(e.payload->'tasks')='array'
       then e.payload->'tasks' else '[]'::jsonb end
 ) as t(value)
 where e.event_type='app_state' and t.value->>'id' is not null
   and length(t.value->>'id') between 1 and 180
 order by t.value->>'id',e.sequence asc
)
insert into public.promysel_task_scopes(task_id,field_id,first_sequence,scope_source)
select task_id,field_id,sequence,'legacy-earliest-field-event'
from first_seen on conflict(task_id) do nothing;

create or replace function app_private.promysel_guard_task_field_v204()
returns trigger language plpgsql security definer set search_path='' as $guard$
declare item jsonb; retained jsonb:='[]'::jsonb;
  task_id text; task_field text; owner_field text; creator text;
begin
 if new.event_type<>'app_state' or jsonb_typeof(new.payload->'tasks')<>'array' then
   return new;
 end if;
 for item in select value from jsonb_array_elements(new.payload->'tasks') loop
   task_id:=item->>'id';task_field:=item->>'fieldId';creator:=item->>'createdById';
   if task_id is null or length(task_id) not between 1 and 180 then continue;end if;
   -- Explicit cross-field rows are rejected without modifying other field data.
   if task_field is not null and task_field<>new.field_id then continue;end if;
   select s.field_id into owner_field from public.promysel_task_scopes s where s.task_id=task_id;
   if owner_field is null then
     -- An old client has no fieldId on new tasks. The creator must currently
     -- belong to this field; otherwise quarantine the row, don't relabel it.
     if task_field is null and not exists (
       select 1 from public.field_memberships m where m.field_id=new.field_id
         and m.user_id::text=creator and m.approved and not m.blocked
     ) then continue;end if;
     insert into public.promysel_task_scopes(task_id,field_id,scope_source)
       values(task_id,new.field_id,case when task_field is null
         then 'verified-creator-legacy-client' else 'explicit-client-field' end)
       on conflict(task_id) do nothing;
     select s.field_id into owner_field from public.promysel_task_scopes s where s.task_id=task_id;
   end if;
   if owner_field=new.field_id then
     retained:=retained||jsonb_build_array(item||jsonb_build_object('fieldId',new.field_id));
   end if;
 end loop;
 new.payload:=jsonb_set(new.payload,'{tasks}',retained,true);
 return new;
exception when others then
 raise exception 'Невозможно проверить принадлежность заданий месторождению (SQLSTATE %)',sqlstate;
end $guard$;
drop trigger if exists zz_promysel_guard_task_field_v204 on public.sync_events;
create trigger zz_promysel_guard_task_field_v204 before insert on public.sync_events
for each row when (new.event_type='app_state')
execute function app_private.promysel_guard_task_field_v204();

commit;
