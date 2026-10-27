
create table public.record_action_audit(
 id bigint generated always as identity primary key,
 record_id text not null references public.field_records(id) on delete restrict,
 field_id text not null references public.oil_fields(id) on delete restrict,
 actor_id uuid not null references auth.users(id),
 action text not null check(action in ('task_completed','problem_application_filed')),
 before_payload jsonb not null,
 after_payload jsonb not null,
 created_at timestamptz not null default now()
);
create index record_action_audit_record_idx on public.record_action_audit(record_id,created_at desc);
create index record_action_audit_field_idx on public.record_action_audit(field_id,created_at desc);
alter table public.record_action_audit enable row level security;
revoke all on public.record_action_audit from public,anon,authenticated;
grant select on public.record_action_audit to authenticated;
create policy record_action_audit_select on public.record_action_audit for select to authenticated
using(app_private.is_member(field_id));

create function public.promysel_mark_task_done(p_record text,p_actor uuid)
returns jsonb language plpgsql security definer set search_path='' as $$
declare r public.field_records%rowtype; after_state jsonb;
begin
 select * into r from public.field_records where id=p_record for update;
 if not found or r.kind<>'task' then raise exception 'Задание не найдено';end if;
 if not exists(select 1 from public.field_memberships m where m.user_id=p_actor
 and m.field_id=r.field_id and m.approved and not m.blocked and
 m.role in ('operator','engineer','shopChief')) then
 raise exception 'Нет права выполнять задание';end if;
 if coalesce(r.payload->>'status','active') not in ('active','assigned') then
 raise exception 'Задание уже завершено или неактивно';end if;
 after_state=r.payload||jsonb_build_object('status','done','completedAt',now(),'completedBy',p_actor::text);
 update public.field_records set payload=after_state,updated_at=now() where id=p_record;
 insert into public.record_action_audit(record_id,field_id,actor_id,action,before_payload,after_payload)
 values(r.id,r.field_id,p_actor,'task_completed',r.payload,after_state);
 return jsonb_build_object('status','done','taskId',r.id);
end $$;
revoke all on function public.promysel_mark_task_done(text,uuid) from public,anon,authenticated;
grant execute on function public.promysel_mark_task_done(text,uuid) to service_role;

create function public.promysel_submit_problem_application(p_record text,p_actor uuid)
returns jsonb language plpgsql security definer set search_path='' as $$
declare r public.field_records%rowtype; after_state jsonb;
begin
 select * into r from public.field_records where id=p_record for update;
 if not found or r.kind<>'problem' then raise exception 'Проблема не найдена';end if;
 if not exists(select 1 from public.field_memberships m where m.user_id=p_actor and
 m.field_id=r.field_id and m.approved and not m.blocked and m.role='dispatcher') then
 raise exception 'Подача заявки доступна только диспетчеру';end if;
 if coalesce(r.payload->>'status','active')='resolved' then raise exception 'Проблема уже закрыта';end if;
 if coalesce((r.payload->>'applicationFiled')::boolean,false) then raise exception 'Заявка уже подана';end if;
 after_state=r.payload||jsonb_build_object('applicationFiled',true,'applicationAt',now(),'applicationBy',p_actor::text);
 update public.field_records set payload=after_state,updated_at=now() where id=p_record;
 insert into public.record_action_audit(record_id,field_id,actor_id,action,before_payload,after_payload)
 values(r.id,r.field_id,p_actor,'problem_application_filed',r.payload,after_state);
 return jsonb_build_object('status','filed','problemId',r.id);
end $$;
revoke all on function public.promysel_submit_problem_application(text,uuid) from public,anon,authenticated;
grant execute on function public.promysel_submit_problem_application(text,uuid) to service_role;
