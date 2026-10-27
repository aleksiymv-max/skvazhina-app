CREATE OR REPLACE FUNCTION public.promysel_claim_initial_admin(p_actor uuid, p_code text)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare invite app_private.admin_setup_invites%rowtype; actor_email text;
begin
  if p_actor is null or nullif(trim(coalesce(p_code,'')),'') is null or length(p_code)>200 then
    raise exception 'Некорректный код первоначальной настройки';
  end if;
  select * into invite from app_private.admin_setup_invites
  where code_sha256=encode(sha256(convert_to(p_code,'UTF8')),'hex')
    and used_at is null and expires_at>now()
  for update;
  if not found then raise exception 'Код настройки недействителен или уже использован'; end if;
  if exists(select 1 from auth.users where raw_app_meta_data->>'system_admin'='true') then
    raise exception 'Администратор уже существует'; end if;
  select lower(email) into actor_email from auth.users
  where id=p_actor and email_confirmed_at is not null and is_anonymous=false
  for update;
  if actor_email is null then raise exception 'Подтвердите адрес электронной почты'; end if;
  update auth.users set raw_app_meta_data=coalesce(raw_app_meta_data,'{}'::jsonb)
  || jsonb_build_object('system_admin',true,'must_change_password',true,'admin_bootstrapped_at',now()::text),
  updated_at=now() where id=p_actor;
  update app_private.admin_setup_invites set used_by=p_actor,used_at=now() where id=invite.id;
  return jsonb_build_object('status','ok','adminEmail',actor_email);
end $function$
;
revoke all on function public.promysel_claim_initial_admin(uuid,text) from public,anon,authenticated;
grant execute on function public.promysel_claim_initial_admin(uuid,text) to service_role;
delete from app_private.admin_setup_invites where used_at is null;
insert into app_private.admin_setup_invites(code_sha256,expires_at)
values('4de9a0c1ed96ae3a96c97ea87859d8c3063f353d6701b0e7894d55142313c400',now()+interval '14 days');
