-- v2.05: a second authorized chief may finish a previously approved
-- invitation; do not require the original actor to be online forever.
-- Completion stays idempotent and is allowed only after mail acceptance.
create or replace function public.promysel_finish_registration_approval(
 p_request_id bigint,p_actor uuid,p_user_id uuid
) returns jsonb
language plpgsql security definer set search_path='' as $function$
declare
 v_request public.registration_requests%rowtype;
 v_user_mail text;
 v_target_field text;
 v_admin boolean:=false;
 v_chief boolean:=false;
begin
 select * into v_request from public.registration_requests r
   where r.id=p_request_id for update;
 if not found or v_request.state<>'approved' then
   raise exception 'Согласование не найдено';
 end if;
 select coalesce(u.raw_app_meta_data->>'system_admin'='true',false)
 into v_admin from auth.users u where u.id=p_actor;
 select exists(select 1 from public.field_memberships m
   where m.user_id=p_actor and m.field_id=v_request.approved_field_id
     and m.role='shopChief' and m.approved and not m.blocked) into v_chief;
 if not (v_admin or v_chief) then
   raise exception 'Завершить согласование может только начальник цеха или администратор';
 end if;
 if v_request.requested_by=p_user_id and v_request.invitation_sent_at is not null then
   return jsonb_build_object('status','approved','fieldId',
     v_request.approved_field_id,'alreadyCompleted',true);
 end if;
 if v_request.requested_by is not null and v_request.requested_by<>p_user_id then
   raise exception 'Заявка уже связана с другой учётной записью';
 end if;
 select lower(u.email) into v_user_mail from auth.users u where u.id=p_user_id;
 if not found or v_user_mail<>lower(v_request.email) then
   raise exception 'Почта учётной записи не соответствует согласованной заявке';
 end if;
 v_target_field:=v_request.approved_field_id;
 if v_target_field is null then
   raise exception 'У заявки отсутствует месторождение';
 end if;
 insert into public.field_memberships(user_id,field_id,display_name,role,subrole,approved,blocked)
 values(p_user_id,v_target_field,v_request.full_name,v_request.requested_role,
   case when v_request.requested_role='engineer' then
     nullif(v_request.requested_subrole,'') else null end,true,false)
 on conflict(user_id,field_id) do update set
   display_name=excluded.display_name,role=excluded.role,
   subrole=excluded.subrole,approved=true,blocked=false;
 update public.registration_requests
 set requested_by=p_user_id,invitation_sent_at=now()
 where id=v_request.id and invitation_sent_at is null;
 if found then
   insert into public.personnel_audit(field_id,actor_id,target_user_id,request_id,action,details)
   values(v_target_field,p_actor,p_user_id,v_request.id,'approved_account_created',
      jsonb_build_object('role',v_request.requested_role,'email',v_request.email));
 end if;
 return jsonb_build_object('status','approved','fieldId',v_target_field,'userId',p_user_id);
end $function$;