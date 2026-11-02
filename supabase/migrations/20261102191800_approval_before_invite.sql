-- Registration is approval-first: no Auth user and no email at application time.
-- Invitation happens only from the authenticated admin/chief approval Edge functions.
ALTER TABLE public.registration_requests ALTER COLUMN requested_by DROP NOT NULL;
ALTER TABLE public.registration_requests ADD COLUMN IF NOT EXISTS approved_field_id text REFERENCES public.oil_fields(id) ON DELETE RESTRICT;
ALTER TABLE public.registration_requests ADD COLUMN IF NOT EXISTS invitation_sent_at timestamptz;

CREATE OR REPLACE FUNCTION public.promysel_finish_registration_approval(p_request_id bigint, p_actor uuid, p_user_id uuid)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare
 r public.registration_requests%rowtype;
 user_mail text;
 target_field text;
begin
 select * into r from public.registration_requests where id=p_request_id for update;
 if not found or r.state <> 'approved' or r.decided_by<>p_actor then
   raise exception 'Согласование не найдено или выполнено другим руководителем';
 end if;
 if r.requested_by=p_user_id and r.invitation_sent_at is not null then
    return jsonb_build_object('status','approved','fieldId',r.approved_field_id,'alreadyCompleted',true);
 end if;
 if r.requested_by is not null and r.requested_by<>p_user_id then
   raise exception 'Заявка связана с другой учётной записью';
 end if;
 select lower(email) into user_mail from auth.users where id=p_user_id;
 if not found or user_mail<>lower(r.email) then
   raise exception 'Учётная запись не соответствует согласованной почте';
 end if;
 target_field=r.approved_field_id;
 if target_field is null then raise exception 'У согласованной заявки отсутствует месторождение'; end if;
 insert into public.field_memberships(user_id,field_id,display_name,role,subrole,approved,blocked)
 values(p_user_id,target_field,r.full_name,r.requested_role,
   case when r.requested_role='engineer' then nullif(r.requested_subrole,'') else null end,true,false)
 on conflict(user_id,field_id) do update set
 display_name=excluded.display_name,role=excluded.role,subrole=excluded.subrole,
 approved=true,blocked=false;
 update public.registration_requests set requested_by=p_user_id,invitation_sent_at=now() where id=r.id;
 insert into public.personnel_audit(field_id,actor_id,target_user_id,request_id,action,details)
 values(target_field,p_actor,p_user_id,r.id,'approved_account_created',
  jsonb_build_object('role',r.requested_role,'email',r.email));
 return jsonb_build_object('status','approved','fieldId',target_field,'userId',p_user_id);
end $function$
;
REVOKE ALL ON FUNCTION public.promysel_finish_registration_approval(bigint,uuid,uuid) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.promysel_finish_registration_approval(bigint,uuid,uuid) TO service_role;

CREATE OR REPLACE FUNCTION public.promysel_start_registration_approval(p_request_id bigint, p_actor uuid)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare
 r public.registration_requests%rowtype;
 system_actor boolean := false;
 chief_actor boolean := false;
 target_field text;
 already uuid;
begin
 select * into r from public.registration_requests where id=p_request_id for update;
 if not found or (r.state <> 'pending' and not (r.state='approved' and r.invitation_sent_at is null)) then
   raise exception 'Заявка не найдена, отклонена или уже приглашена';
 end if;
 select coalesce(raw_app_meta_data->>'system_admin'='true',false) into system_actor
 from auth.users where id=p_actor;
 if not found then raise exception 'Пользователь не найден'; end if;
 if r.field_id is null then
   if not system_actor then raise exception 'Первого начальника цеха согласует только системный администратор'; end if;
 else
   select exists(select 1 from public.field_memberships
     where user_id=p_actor and field_id=r.field_id
       and role='shopChief' and approved and not blocked) into chief_actor;
   if not (system_actor or chief_actor) then raise exception 'Согласование доступно начальнику цеха или администратору'; end if;
 end if;
 if r.state='pending' then
   if r.field_id is null then
     if r.requested_role<>'shopChief' or nullif(btrim(r.proposed_field_name),'') is null then
       raise exception 'Новое месторождение может запросить только начальник цеха';
     end if;
     target_field='field-'||gen_random_uuid()::text;
     insert into public.oil_fields(id,name) values(target_field,btrim(r.proposed_field_name));
   else
     target_field=r.field_id;
   end if;
   update public.registration_requests
     set state='approved',decided_by=p_actor,decided_at=now(),approved_field_id=target_field
     where id=r.id;
   insert into public.personnel_audit(field_id,actor_id,target_user_id,request_id,action,details)
     values(target_field,p_actor,r.requested_by,r.id,'approve_request',
       jsonb_build_object('role',r.requested_role,'email',r.email));
 else
   target_field=r.approved_field_id;
   if target_field is null then raise exception 'Не назначено месторождение для одобренной заявки';end if;
 end if;
 select id into already from auth.users where lower(email)=lower(r.email) limit 1;
 return jsonb_build_object('status','approved','fieldId',target_field,'email',r.email,
   'fullName',r.full_name,'role',r.requested_role,'existingUserId',already,
   'requestId',r.id);
end $function$
;
REVOKE ALL ON FUNCTION public.promysel_start_registration_approval(bigint,uuid) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.promysel_start_registration_approval(bigint,uuid) TO service_role;
