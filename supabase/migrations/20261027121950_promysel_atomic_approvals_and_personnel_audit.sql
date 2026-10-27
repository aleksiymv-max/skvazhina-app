
create unique index if not exists oil_fields_name_ci on public.oil_fields(lower(name));
create table public.personnel_audit (
 id bigint generated always as identity primary key,
 field_id text references public.oil_fields(id) on delete restrict,
 actor_id uuid not null references auth.users(id),
 target_user_id uuid references auth.users(id),
 request_id bigint references public.registration_requests(id),
 action text not null check (action in ('approve','reject','role_change','block','unblock')),
 details jsonb not null default '{}'::jsonb,
 created_at timestamptz not null default now()
);
create index personnel_audit_field_idx on public.personnel_audit(field_id,created_at desc);
alter table public.personnel_audit enable row level security;
revoke all on public.personnel_audit from public,anon,authenticated;
grant select on public.personnel_audit to authenticated;
create policy personnel_audit_select on public.personnel_audit for select to authenticated
using(actor_id=(select auth.uid()) or (field_id is not null and app_private.can_approve_registration(field_id)));

-- This RPC is callable by the server-side service_role only. It rejects unverified applicants and
-- performs the field creation, personnel creation, audit, and request decision in ONE transaction.
create function public.promysel_approve_registration(p_request_id bigint,p_actor uuid)
returns jsonb language plpgsql security definer set search_path='' as $$
declare
 r public.registration_requests%rowtype;
 admin_actor boolean:=false;
 scoped_chief boolean:=false;
 v_field text;
 v_field_name text;
begin
 select * into r from public.registration_requests where id=p_request_id for update;
 if not found or r.state <> 'pending' then raise exception 'Заявка не найдена или уже рассмотрена'; end if;
 select coalesce(u.raw_app_meta_data->>'system_admin'='true',false) into admin_actor
 from auth.users u where u.id=p_actor;
 if not found then raise exception 'Администратор или начальник не найден'; end if;
 if r.field_id is not null then
   select exists(select 1 from public.field_memberships m where m.user_id=p_actor and m.field_id=r.field_id
       and m.role='shopChief' and m.approved and not m.blocked) into scoped_chief;
 end if;
 if r.field_id is null and not admin_actor then raise exception 'Создание месторождения подтверждает только администратор'; end if;
 if r.field_id is not null and not (admin_actor or scoped_chief) then raise exception 'Нет прав согласовать заявку'; end if;
 if not exists(select 1 from auth.users u where u.id=r.requested_by
        and u.email_confirmed_at is not null and lower(u.email)=lower(r.email)) then
     raise exception 'Электронная почта заявителя не подтверждена'; end if;
 if r.field_id is null then
    v_field_name=nullif(btrim(r.proposed_field_name),'');
    if v_field_name is null or length(v_field_name)>200 then raise exception 'Некорректное название месторождения'; end if;
    if r.requested_role <> 'shopChief' then raise exception 'Новое месторождение открывает заявка начальника'; end if;
    v_field='field-'||gen_random_uuid()::text;
    insert into public.oil_fields(id,name) values(v_field,v_field_name);
 else
    v_field=r.field_id;
 end if;
 insert into public.field_memberships(user_id,field_id,display_name,role,subrole,approved,blocked)
 values(r.requested_by,v_field,r.full_name,r.requested_role,
        case when r.requested_role='engineer' then nullif(r.requested_subrole,'') else null end,true,false)
 on conflict(user_id,field_id) do update
 set display_name=excluded.display_name,role=excluded.role,subrole=excluded.subrole,approved=true,blocked=false;
 update public.registration_requests set state='approved',decided_by=p_actor,decided_at=now()
 where id=p_request_id and state='pending';
 insert into public.personnel_audit(field_id,actor_id,target_user_id,request_id,action,details)
 values(v_field,p_actor,r.requested_by,r.id,'approve',jsonb_build_object('role',r.requested_role,'subrole',r.requested_subrole));
 return jsonb_build_object('status','approved','fieldId',v_field,'userId',r.requested_by);
end $$;
revoke all on function public.promysel_approve_registration(bigint,uuid) from public,anon,authenticated;
grant execute on function public.promysel_approve_registration(bigint,uuid) to service_role;

create function public.promysel_reject_registration(p_request_id bigint,p_actor uuid,p_note text default null)
returns jsonb language plpgsql security definer set search_path='' as $$
declare r public.registration_requests%rowtype; admin_actor boolean:=false;
begin
 select * into r from public.registration_requests where id=p_request_id for update;
 if not found or r.state<>'pending' then raise exception 'Заявка не найдена или уже рассмотрена'; end if;
 select coalesce(u.raw_app_meta_data->>'system_admin'='true',false)
 into admin_actor from auth.users u where u.id=p_actor;
 if not admin_actor and not exists(select 1 from public.field_memberships m where
 m.user_id=p_actor and m.field_id=r.field_id and m.role='shopChief' and m.approved and not m.blocked)
 then raise exception 'Нет прав отклонить заявку';end if;
 update public.registration_requests set state='rejected',decided_by=p_actor,decided_at=now() where id=r.id;
 insert into public.personnel_audit(field_id,actor_id,target_user_id,request_id,action,details)
 values(r.field_id,p_actor,r.requested_by,r.id,'reject',jsonb_build_object('note',left(coalesce(p_note,''),1000)));
 return jsonb_build_object('status','rejected','requestId',r.id);
end $$;
revoke all on function public.promysel_reject_registration(bigint,uuid,text) from public,anon,authenticated;
grant execute on function public.promysel_reject_registration(bigint,uuid,text) to service_role;

-- Personnel management is constrained by the 2026 matrix. Only authorized personnel
-- can grant an operational role, and no change grants system-admin or shop-chief privileges.
create function public.promysel_change_role(p_field text,p_actor uuid,p_target uuid,
  p_role text,p_subrole text default null)
returns jsonb language plpgsql security definer set search_path='' as $$
declare actor_role text; actor_subrole text;
begin
 select m.role,m.subrole into actor_role,actor_subrole from public.field_memberships m where
  m.user_id=p_actor and m.field_id=p_field and m.approved and not m.blocked;
 if not found or not (actor_role='shopChief' or (actor_role='engineer' and
  actor_subrole in ('master','leadingGeologist','leadingTechnologist'))) then
  raise exception 'Нет прав изменять должности сотрудников';end if;
 if p_actor=p_target then raise exception 'Нельзя менять собственную роль';end if;
 if p_role not in ('operator','dispatcher','engineer') then
  raise exception 'Назначение начальника и администратора через кадровое изменение запрещено';end if;
 if p_role='engineer' and p_subrole not in ('master','geologist','leadingGeologist','technologist','leadingTechnologist')
 then raise exception 'Не выбрана должность ИТР';end if;
 update public.field_memberships set role=p_role,subrole=case when p_role='engineer' then p_subrole else null end
 where user_id=p_target and field_id=p_field and approved and not blocked and role not in ('admin','shopChief');
 if not found then raise exception 'Сотрудник не найден или защищён от редактирования';end if;
 insert into public.personnel_audit(field_id,actor_id,target_user_id,action,details)
 values(p_field,p_actor,p_target,'role_change',jsonb_build_object('role',p_role,'subrole',p_subrole));
 return jsonb_build_object('status','ok','fieldId',p_field,'userId',p_target,'role',p_role);
end $$;
revoke all on function public.promysel_change_role(text,uuid,uuid,text,text) from public,anon,authenticated;
grant execute on function public.promysel_change_role(text,uuid,uuid,text,text) to service_role;
