-- STAGING ONLY. Do not deploy until an isolated Supabase project has passed
-- RLS tests, migration/backfill rehearsals, and rollback verification.
-- Canonical task identity must precede task photo evidence.
begin;

create table public.work_tasks (
  field_id text not null references public.oil_fields(id) on delete restrict,
  id text not null check (length(id) between 1 and 128),
  title text not null check (length(btrim(title)) between 1 and 300),
  description text not null default '' check (length(description) <= 10000),
  target_type text not null check (target_type in ('personal','area','pad')),
  target_id text not null check (length(target_id) between 1 and 128),
  assigned_to uuid references auth.users(id) on delete restrict,
  created_by uuid not null references auth.users(id) on delete restrict,
  status text not null default 'active' check (status in ('active','awaitingConfirmation','confirmed')),
  created_at timestamptz not null default now(),
  completed_at timestamptz,
  completed_by uuid references auth.users(id) on delete restrict,
  reviewed_at timestamptz,
  reviewed_by uuid references auth.users(id) on delete restrict,
  review_note text,
  primary key(field_id,id),
  check ((target_type='personal' and assigned_to is not null and target_id=assigned_to::text)
      or (target_type in ('area','pad') and assigned_to is null))
);
create index work_tasks_created_by_idx on public.work_tasks(created_by);
create index work_tasks_assigned_idx on public.work_tasks(field_id,assigned_to,status) where assigned_to is not null;
create index work_tasks_field_status_idx on public.work_tasks(field_id,status,created_at desc);

-- Explicit common-task audience; field membership alone is insufficient.
create table public.work_task_assignees (
  field_id text not null,
  task_id text not null,
  user_id uuid not null,
  assigned_by uuid not null default auth.uid(),
  assigned_at timestamptz not null default now(),
  primary key(field_id,task_id,user_id),
  foreign key(field_id,task_id) references public.work_tasks(field_id,id) on delete restrict,
  foreign key(user_id,field_id) references public.field_memberships(user_id,field_id) on delete restrict,
  foreign key(assigned_by) references auth.users(id) on delete restrict
);
create index work_task_assignees_user_idx on public.work_task_assignees(user_id,field_id);
alter table public.work_task_assignees enable row level security;
revoke all on public.work_task_assignees from anon,authenticated;
grant select,insert on public.work_task_assignees to authenticated;
create policy work_task_assignees_read on public.work_task_assignees for select to authenticated
using (app_private.is_member(field_id) and
  (user_id=(select auth.uid()) or app_private.can_manage_tasks(field_id)));
create policy work_task_assignees_insert on public.work_task_assignees for insert to authenticated
with check (
  assigned_by=(select auth.uid()) and app_private.can_manage_tasks(field_id)
  and exists(select 1 from public.work_tasks t
    where t.field_id=work_task_assignees.field_id and t.id=work_task_assignees.task_id
      and t.target_type in ('area','pad') and t.status='active')
  and exists(select 1 from public.field_memberships m
    where m.field_id=work_task_assignees.field_id and m.user_id=work_task_assignees.user_id
      and m.approved and not m.blocked
      and m.role in ('operator','engineer','shopChief'))
);

create function app_private.can_view_task(p_field text,p_task text)
returns boolean language sql stable security definer set search_path='' as $$
  select app_private.is_member(p_field) and exists (
    select 1 from public.work_tasks t where t.field_id=p_field and t.id=p_task
    and (app_private.can_manage_tasks(p_field)
      or (t.target_type='personal' and t.assigned_to=(select auth.uid()))
      or (t.target_type in ('area','pad') and app_private.can_walk(p_field)
        and exists(select 1 from public.work_task_assignees a
          where a.field_id=t.field_id and a.task_id=t.id and a.user_id=(select auth.uid()))))
  )
$$;
create function app_private.can_attach_task(p_field text,p_task text)
returns boolean language sql stable security definer set search_path='' as $$
  select app_private.is_member(p_field) and exists (
    select 1 from public.work_tasks t where t.field_id=p_field and t.id=p_task
      and t.status in ('active','awaitingConfirmation')
      and ((t.target_type='personal' and t.assigned_to=(select auth.uid()))
        or (t.target_type in ('area','pad') and app_private.can_walk(p_field)
          and exists(select 1 from public.work_task_assignees a
            where a.field_id=t.field_id and a.task_id=t.id and a.user_id=(select auth.uid()))))
  )
$$;
revoke all on function app_private.can_view_task(text,text) from public,anon;
revoke all on function app_private.can_attach_task(text,text) from public,anon;
grant execute on function app_private.can_view_task(text,text) to authenticated;
grant execute on function app_private.can_attach_task(text,text) to authenticated;

create function app_private.validate_task_target() returns trigger
language plpgsql security invoker set search_path='' as $$
begin
  if new.created_by is distinct from (select auth.uid())
     or not app_private.can_manage_tasks(new.field_id) then
    raise exception 'Task creation not authorized';
  end if;
  if new.target_type='personal' then
    if not exists(select 1 from public.field_memberships m
      where m.field_id=new.field_id and m.user_id=new.assigned_to
        and m.approved and not m.blocked) then
      raise exception 'Assignee not approved for field';
    end if;
  elsif new.target_type='area' then
    if not exists(select 1 from public.production_areas a
      where a.field_id=new.field_id and a.id=new.target_id) then
      raise exception 'Area does not belong to field';
    end if;
  elsif new.target_type='pad' then
    if not exists(select 1 from public.pads p
      where p.field_id=new.field_id and p.id=new.target_id) then
      raise exception 'Pad does not belong to field';
    end if;
  end if;
  return new;
end $$;
create trigger validate_work_task_target before insert on public.work_tasks
for each row execute function app_private.validate_task_target();
revoke all on function app_private.validate_task_target() from public,anon,authenticated;

alter table public.work_tasks enable row level security;
revoke all on public.work_tasks from anon,authenticated;
grant select,insert on public.work_tasks to authenticated;
create policy work_tasks_read on public.work_tasks for select to authenticated
using (app_private.can_view_task(field_id,id));
create policy work_tasks_create on public.work_tasks for insert to authenticated
with check (created_by=(select auth.uid()) and status='active'
  and completed_at is null and completed_by is null
  and reviewed_at is null and reviewed_by is null and review_note is null
  and app_private.can_manage_tasks(field_id));

create table public.work_task_events (
  event_id bigint generated always as identity primary key,
  field_id text not null,
  task_id text not null,
  actor_id uuid not null references auth.users(id) on delete restrict,
  event_type text not null check(event_type in ('completed','confirmed','rejected')),
  note text,
  created_at timestamptz not null default now(),
  foreign key(field_id,task_id) references public.work_tasks(field_id,id) on delete restrict
);
create index work_task_events_task_idx on public.work_task_events(field_id,task_id,created_at desc);
create index work_task_events_actor_idx on public.work_task_events(actor_id);
alter table public.work_task_events enable row level security;
revoke all on public.work_task_events from anon,authenticated;
grant select on public.work_task_events to authenticated;
create policy work_task_events_read on public.work_task_events for select to authenticated
using (app_private.can_view_task(field_id,task_id));

create function public.promysel_complete_task(p_field text,p_task text)
returns jsonb language plpgsql security definer set search_path='' as $$
declare t public.work_tasks%rowtype; v_actor uuid:=(select auth.uid());
begin
  if v_actor is null or not app_private.can_attach_task(p_field,p_task) then
    raise exception 'Not allowed to complete this task';
  end if;
  select * into t from public.work_tasks where field_id=p_field and id=p_task for update;
  if not found then raise exception 'Task not found'; end if;
  if t.status='awaitingConfirmation' and t.completed_by=v_actor then
    return jsonb_build_object('status',t.status,'taskId',p_task);
  end if;
  if t.status<>'active' then raise exception 'Invalid task transition'; end if;
  update public.work_tasks set status='awaitingConfirmation',completed_by=v_actor,
    completed_at=now(),reviewed_by=null,reviewed_at=null,review_note=null
  where field_id=p_field and id=p_task;
  insert into public.work_task_events(field_id,task_id,actor_id,event_type)
  values(p_field,p_task,v_actor,'completed');
  return jsonb_build_object('status','awaitingConfirmation','taskId',p_task);
end $$;

create function public.promysel_review_task(p_field text,p_task text,p_approve boolean,p_note text default null)
returns jsonb language plpgsql security definer set search_path='' as $$
declare t public.work_tasks%rowtype; v_actor uuid:=(select auth.uid());
begin
  if v_actor is null or not app_private.is_member(p_field) then
    raise exception 'Not a current member';
  end if;
  select * into t from public.work_tasks where field_id=p_field and id=p_task for update;
  if not found then raise exception 'Task not found'; end if;
  if not app_private.can_manage_tasks(p_field)
     or (t.created_by<>v_actor and app_private.member_role(p_field)<>'shopChief') then
    raise exception 'Only the author or shop chief may review';
  end if;
  if t.status<>'awaitingConfirmation' then raise exception 'Task not awaiting review'; end if;
  if p_approve is null then raise exception 'Review decision required'; end if;
  if not p_approve and (nullif(btrim(coalesce(p_note,'')),'') is null or length(p_note)>2000) then
    raise exception 'Rejection reason required';
  end if;
  update public.work_tasks
    set status=case when p_approve then 'confirmed' else 'active' end,
      reviewed_by=v_actor,reviewed_at=now(),
      review_note=case when p_approve then null else p_note end,
      completed_at=case when p_approve then completed_at else null end,
      completed_by=case when p_approve then completed_by else null end
    where field_id=p_field and id=p_task;
  insert into public.work_task_events(field_id,task_id,actor_id,event_type,note)
    values(p_field,p_task,v_actor,case when p_approve then 'confirmed' else 'rejected' end,
      case when p_approve then null else p_note end);
  return jsonb_build_object('status',case when p_approve then 'confirmed' else 'active' end,'taskId',p_task);
end $$;
revoke all on function public.promysel_complete_task(text,text) from public,anon,authenticated;
revoke all on function public.promysel_review_task(text,text,boolean,text) from public,anon,authenticated;
grant execute on function public.promysel_complete_task(text,text) to authenticated;
grant execute on function public.promysel_review_task(text,text,boolean,text) to authenticated;

create table public.task_evidence (
  id uuid primary key default gen_random_uuid(),
  field_id text not null,
  task_id text not null,
  uploaded_by uuid not null references auth.users(id) on delete restrict,
  object_path text not null unique,
  mime_type text not null check(mime_type in ('image/jpeg','image/png','image/webp')),
  file_size_bytes bigint not null check(file_size_bytes between 1 and 10485760),
  created_at timestamptz not null default now(),
  foreign key(field_id,task_id) references public.work_tasks(field_id,id) on delete restrict,
  check (object_path='evidence/'||id::text)
);
create index task_evidence_task_idx on public.task_evidence(field_id,task_id,created_at desc);
create index task_evidence_uploader_idx on public.task_evidence(uploaded_by);
alter table public.task_evidence enable row level security;
revoke all on public.task_evidence from anon,authenticated;
grant select,insert on public.task_evidence to authenticated;
create policy task_evidence_read on public.task_evidence for select to authenticated
using (app_private.can_view_task(field_id,task_id));
create policy task_evidence_add on public.task_evidence for insert to authenticated
with check (uploaded_by=(select auth.uid()) and app_private.can_attach_task(field_id,task_id));

-- Bucket is private. A collision with an existing bucket is a hard stop.
do $$
begin
 if exists(select 1 from storage.buckets where id='promysel-task-evidence') then
   raise exception 'Existing task-evidence bucket must be reviewed manually';
 end if;
 insert into storage.buckets(id,name,public,file_size_limit,allowed_mime_types)
 values('promysel-task-evidence','promysel-task-evidence',false,10485760,
   array['image/jpeg','image/png','image/webp']);
end $$;
create policy promysel_task_photo_read on storage.objects for select to authenticated
using (bucket_id='promysel-task-evidence' and exists(
  select 1 from public.task_evidence e where e.object_path=name
    and app_private.can_view_task(e.field_id,e.task_id)));
create policy promysel_task_photo_upload on storage.objects for insert to authenticated
with check (bucket_id='promysel-task-evidence' and exists(
  select 1 from public.task_evidence e where e.object_path=name
    and e.uploaded_by=(select auth.uid())
    and app_private.can_attach_task(e.field_id,e.task_id)));
-- No client UPDATE/DELETE grant on tasks/evidence, no Storage UPDATE/DELETE policy.
-- Backfill from legacy app_state and cutover require a separate, audited migration.
commit;
