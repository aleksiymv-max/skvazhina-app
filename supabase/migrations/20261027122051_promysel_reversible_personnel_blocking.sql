
create function public.promysel_set_worker_blocked(p_field text,p_actor uuid,p_target uuid,p_blocked boolean)
returns jsonb language plpgsql security definer set search_path='' as $$
declare actor_role text; actor_subrole text;
begin
 select m.role,m.subrole into actor_role,actor_subrole
 from public.field_memberships m where m.user_id=p_actor and m.field_id=p_field
 and m.approved and not m.blocked;
 if not found or not (actor_role='shopChief' or (actor_role='engineer'
 and actor_subrole in ('master','leadingGeologist','leadingTechnologist')))
 then raise exception 'Недостаточно прав для управления сотрудниками';end if;
 if p_actor=p_target then raise exception 'Нельзя удалить или заблокировать собственную учётную запись';end if;
 update public.field_memberships set blocked=p_blocked where field_id=p_field and user_id=p_target
  and approved and role not in ('shopChief','admin');
 if not found then raise exception 'Сотрудник не найден или обладает защищённой ролью';end if;
 insert into public.personnel_audit(field_id,actor_id,target_user_id,action,details)
 values(p_field,p_actor,p_target,case when p_blocked then 'block' else 'unblock' end,'{}'::jsonb);
 return jsonb_build_object('status','ok','userId',p_target,'blocked',p_blocked);
end $$;
revoke all on function public.promysel_set_worker_blocked(text,uuid,uuid,boolean) from public,anon,authenticated;
grant execute on function public.promysel_set_worker_blocked(text,uuid,uuid,boolean) to service_role;
