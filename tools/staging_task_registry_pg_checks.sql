-- PostgreSQL RLS and RPC smoke tests on synthetic accounts ONLY.
-- Requires staging_task_registry_pg_fixture.sql and staging DDL first.
\set ON_ERROR_STOP on
set role authenticated;
select set_config('request.jwt.claim.sub','00000000-0000-0000-0000-000000000001',false);
insert into public.work_tasks(field_id,id,title,target_type,target_id,assigned_to,created_by)
values('field-a','personal-1','Synthetic personal task','personal',
'00000000-0000-0000-0000-000000000002','00000000-0000-0000-0000-000000000002',
'00000000-0000-0000-0000-000000000001');
insert into public.work_tasks(field_id,id,title,target_type,target_id,created_by)
values('field-a','area-1','Synthetic area task','area','area-a',
'00000000-0000-0000-0000-000000000001');
select public.promysel_assign_task_assignee('field-a','area-1','00000000-0000-0000-0000-000000000002');
do $$ begin
  if (select count(*) from public.work_tasks where field_id='field-a')<>2
  then raise exception 'Chief must see two tasks'; end if;
end $$;
reset role;

set role authenticated;
select set_config('request.jwt.claim.sub','00000000-0000-0000-0000-000000000002',false);
do $$ begin
  if (select count(*) from public.work_tasks where field_id='field-a')<>2
  then raise exception 'Assigned operator must see two tasks'; end if;
end $$;
insert into public.task_evidence(id,field_id,task_id,uploaded_by,object_path,mime_type,file_size_bytes)
values('10000000-0000-0000-0000-000000000001','field-a','personal-1',
'00000000-0000-0000-0000-000000000002',
'evidence/10000000-0000-0000-0000-000000000001','image/jpeg',1024);
insert into storage.objects(bucket_id,name)
values('promysel-task-evidence','evidence/10000000-0000-0000-0000-000000000001');
do $$ begin
  if (select count(*) from storage.objects where bucket_id='promysel-task-evidence')<>1
  then raise exception 'Evidence Storage read denied to assigned operator'; end if;
end $$;
select public.promysel_complete_task('field-a','personal-1');
select public.promysel_complete_task('field-a','personal-1');
do $$ begin
  if (select count(*) from public.work_task_events where task_id='personal-1')<>1
  then raise exception 'Duplicate completion event'; end if;
  begin
    update public.work_tasks set status='confirmed' where id='personal-1';
    raise exception 'Direct task update unexpectedly succeeded';
  exception when insufficient_privilege then null; end;
end $$;
reset role;

set role authenticated;
select set_config('request.jwt.claim.sub','00000000-0000-0000-0000-000000000003',false);
do $$ begin
  if exists(select 1 from public.work_tasks where field_id='field-a')
  then raise exception 'Unassigned operator sees tasks'; end if;
  if exists(select 1 from public.task_evidence)
  then raise exception 'Unassigned operator sees evidence'; end if;
  if exists(select 1 from storage.objects)
  then raise exception 'Unassigned operator sees Storage objects'; end if;
  begin
    perform public.promysel_complete_task('field-a','personal-1');
    raise exception 'Unassigned operator completed task';
  exception when others then
    if sqlerrm='Unassigned operator completed task' then raise; end if;
  end;
  begin
    insert into public.task_evidence(id,field_id,task_id,uploaded_by,object_path,mime_type,file_size_bytes)
    values('10000000-0000-0000-0000-000000000002','field-a','personal-1',
    '00000000-0000-0000-0000-000000000003',
    'evidence/10000000-0000-0000-0000-000000000002','image/jpeg',1024);
    raise exception 'Unassigned operator inserted evidence';
  exception when others then
    if sqlerrm='Unassigned operator inserted evidence' then raise; end if;
  end;
end $$;
reset role;

set role authenticated;
select set_config('request.jwt.claim.sub','00000000-0000-0000-0000-000000000005',false);
do $$ begin
  if exists(select 1 from public.work_tasks) then
    raise exception 'Other-field operator sees tasks'; end if;
  if exists(select 1 from storage.objects) then
    raise exception 'Other-field operator sees Storage'; end if;
end $$;
reset role;

set role authenticated;
select set_config('request.jwt.claim.sub','00000000-0000-0000-0000-000000000004',false);
do $$ begin
  if exists(select 1 from public.work_tasks) then
    raise exception 'Blocked operator sees tasks'; end if;
end $$;
reset role;

set role authenticated;
select set_config('request.jwt.claim.sub','00000000-0000-0000-0000-000000000001',false);
select public.promysel_review_task('field-a','personal-1',true,null);
do $$ begin
  if (select status from public.work_tasks where id='personal-1')<>'confirmed'
  then raise exception 'Review did not persist'; end if;
end $$;
reset role;

-- Blocking an assigned employee must revoke both task and photo reads.
update public.field_memberships set blocked=true
where user_id='00000000-0000-0000-0000-000000000002' and field_id='field-a';
set role authenticated;
select set_config('request.jwt.claim.sub','00000000-0000-0000-0000-000000000002',false);
do $$ begin
  if exists(select 1 from public.work_tasks) then
    raise exception 'Blocked assignee still sees tasks'; end if;
  if exists(select 1 from public.task_evidence) then
    raise exception 'Blocked assignee still sees evidence'; end if;
  if exists(select 1 from storage.objects) then
    raise exception 'Blocked assignee still sees Storage'; end if;
end $$;
reset role;
-- A common-task assignment must be revocable only by a current manager.
set role authenticated;
select set_config('request.jwt.claim.sub','00000000-0000-0000-0000-000000000001',false);
insert into public.work_tasks(field_id,id,title,target_type,target_id,created_by)
values('field-a','area-revoke','Synthetic revocation task','area','area-a',
'00000000-0000-0000-0000-000000000001');
select public.promysel_assign_task_assignee('field-a','area-revoke','00000000-0000-0000-0000-000000000003');
reset role;
set role authenticated;
select set_config('request.jwt.claim.sub','00000000-0000-0000-0000-000000000003',false);
do $$ begin
  if not exists(select 1 from public.work_tasks where id='area-revoke')
  then raise exception 'Assigned operator cannot see common task'; end if;
  begin
    perform public.promysel_revoke_task_assignee(
      'field-a','area-revoke','00000000-0000-0000-0000-000000000003');
    raise exception 'Operator revoked own task assignment';
  exception when others then
    if sqlerrm='Operator revoked own task assignment' then raise; end if;
  end;
end $$;
reset role;
set role authenticated;
select set_config('request.jwt.claim.sub','00000000-0000-0000-0000-000000000001',false);
select public.promysel_revoke_task_assignee(
  'field-a','area-revoke','00000000-0000-0000-0000-000000000003');
select public.promysel_revoke_task_assignee(
  'field-a','area-revoke','00000000-0000-0000-0000-000000000003');
do $$ begin
  if (select count(*) from public.work_task_assignee_events
      where task_id='area-revoke' and action='revoked')<>1
  then raise exception 'Revocation must be audited once'; end if;
end $$;
reset role;
set role authenticated;
select set_config('request.jwt.claim.sub','00000000-0000-0000-0000-000000000003',false);
do $$ begin
  if exists(select 1 from public.work_tasks where id='area-revoke')
  then raise exception 'Revoked operator still sees common task'; end if;
end $$;
reset role;

select 'PASS: synthetic PostgreSQL task RLS, Storage, completion and revocation' as result;
