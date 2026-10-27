
create or replace function app_private.member_subrole(p_field text) returns text language sql stable security definer set search_path='' as $$ select m.subrole from public.field_memberships m where m.user_id=(select auth.uid()) and m.field_id=p_field and m.approved and not m.blocked limit 1 $$;
create or replace function app_private.can_structure(p_field text) returns boolean language sql stable security definer set search_path='' as $$
 select app_private.member_role(p_field) in ('shopChief','admin')
 or (app_private.member_role(p_field)='engineer' and app_private.member_subrole(p_field) in ('geologist','leadingGeologist','technologist','leadingTechnologist'))
$$;
create or replace function app_private.can_delete_structure(p_field text) returns boolean language sql stable security definer set search_path='' as $$
 select app_private.member_role(p_field) in ('shopChief','admin')
 or (app_private.member_role(p_field)='engineer' and app_private.member_subrole(p_field) in ('leadingGeologist','leadingTechnologist'))
$$;
create or replace function app_private.can_correct(p_field text) returns boolean language sql stable security definer set search_path='' as $$
 select app_private.member_role(p_field) in ('shopChief','admin')
 or (app_private.member_role(p_field)='engineer' and app_private.member_subrole(p_field) in ('geologist','leadingGeologist','technologist','leadingTechnologist'))
$$;
create or replace function app_private.can_manage_tasks(p_field text) returns boolean language sql stable security definer set search_path='' as $$
 select app_private.member_role(p_field) in ('shopChief','admin','engineer')
$$;
create or replace function app_private.can_resolve_problem(p_field text) returns boolean language sql stable security definer set search_path='' as $$
 select app_private.member_role(p_field) in ('shopChief','admin','engineer','dispatcher')
$$;
create or replace function app_private.can_manage_personnel(p_field text) returns boolean language sql stable security definer set search_path='' as $$
 select app_private.member_role(p_field) in ('shopChief','admin')
 or (app_private.member_role(p_field)='engineer' and app_private.member_subrole(p_field) in ('master','leadingGeologist','leadingTechnologist'))
$$;
create or replace function app_private.can_approve_registration(p_field text) returns boolean language sql stable security definer set search_path='' as $$
 select app_private.member_role(p_field) in ('shopChief','admin')
$$;
create or replace function app_private.can_export(p_field text) returns boolean language sql stable security definer set search_path='' as $$
 select app_private.member_role(p_field) in ('shopChief','admin','engineer')
$$;
revoke all on all functions in schema app_private from public,anon;
grant execute on all functions in schema app_private to authenticated;
drop policy membership_select on public.field_memberships;
create policy membership_select on public.field_memberships for select to authenticated
 using(user_id=(select auth.uid()) or app_private.is_member(field_id));
drop policy registration_select on public.registration_requests;
create policy registration_select on public.registration_requests for select to authenticated
 using(requested_by=(select auth.uid()) or (field_id is not null and app_private.can_approve_registration(field_id)));
drop policy records_insert on public.field_records;
create policy records_insert on public.field_records for insert to authenticated
 with check(created_by=(select auth.uid()) and app_private.is_member(field_id) and
 case kind when 'task' then app_private.can_manage_tasks(field_id)
 when 'problem' then app_private.can_walk(field_id)
 when 'annulus_pressure' then app_private.can_walk(field_id)
 when 'training' then owner_id=(select auth.uid())
 when 'notification' then owner_id=(select auth.uid())
 when 'equipment' then app_private.can_structure(field_id)
 when 'repair' then app_private.can_structure(field_id)
 else false end);
drop policy records_update on public.field_records;
create policy records_update on public.field_records for update to authenticated
 using (app_private.is_member(field_id) and
 case kind when 'task' then app_private.can_manage_tasks(field_id)
 when 'problem' then app_private.can_resolve_problem(field_id)
 when 'annulus_pressure' then app_private.can_correct(field_id)
 when 'training' then owner_id=(select auth.uid())
 when 'notification' then owner_id=(select auth.uid())
 when 'equipment' then app_private.can_structure(field_id)
 when 'repair' then app_private.can_structure(field_id)
 else false end)
 with check (app_private.is_member(field_id) and
 case kind when 'task' then app_private.can_manage_tasks(field_id)
 when 'problem' then app_private.can_resolve_problem(field_id)
 when 'annulus_pressure' then app_private.can_correct(field_id)
 when 'training' then owner_id=(select auth.uid())
 when 'notification' then owner_id=(select auth.uid())
 when 'equipment' then app_private.can_structure(field_id)
 when 'repair' then app_private.can_structure(field_id)
 else false end);
create function app_private.field_record_immutable_guard() returns trigger language plpgsql security invoker set search_path='' as $$
begin
 if new.id is distinct from old.id or new.field_id is distinct from old.field_id
    or new.kind is distinct from old.kind or new.created_by is distinct from old.created_by
    or new.owner_id is distinct from old.owner_id or new.well_id is distinct from old.well_id
 then raise exception 'Record identity and ownership cannot be changed'; end if;
 new.updated_at=now();
 return new;
end $$;
create trigger field_record_guard before update on public.field_records
for each row execute function app_private.field_record_immutable_guard();
drop policy sync_insert on public.sync_events;
create policy sync_insert on public.sync_events for insert to authenticated with check (
 actor_id=(select auth.uid()) and app_private.is_member(field_id)
 and case event_type
 when 'measurement' then app_private.can_walk(field_id)
 when 'app_state' then app_private.can_structure(field_id)
 when 'task' then app_private.can_manage_tasks(field_id)
 when 'problem' then app_private.can_walk(field_id) or app_private.can_resolve_problem(field_id)
 when 'annulus_pressure' then app_private.can_walk(field_id)
 when 'training' then true
 when 'notification' then true
 when 'equipment' then app_private.can_structure(field_id)
 when 'repair' then app_private.can_structure(field_id)
 else false end);
alter table public.walk_measurements add column correction_reason text;
revoke insert on public.measurement_corrections from authenticated;
create function app_private.measurement_audit_guard() returns trigger language plpgsql security definer set search_path='' as $$
begin
 if (select auth.uid()) is null or not app_private.can_correct(old.field_id) then
  raise exception 'Historical correction is not permitted';
 end if;
 if new.id is distinct from old.id or new.field_id is distinct from old.field_id
 or new.pad_id is distinct from old.pad_id or new.well_id is distinct from old.well_id
 or new.actor_id is distinct from old.actor_id or new.created_at is distinct from old.created_at
 or new.measured_at is distinct from old.measured_at then
  raise exception 'Historical measurement identity cannot be changed';
 end if;
 if new.payload is not distinct from old.payload then raise exception 'No measurement values changed'; end if;
 if nullif(btrim(coalesce(new.correction_reason,'')),'') is null or length(new.correction_reason)>2000
 then raise exception 'Correction reason is required'; end if;
 insert into public.measurement_corrections(measurement_id,field_id,actor_id,reason,before_payload,after_payload)
 values(old.id,old.field_id,(select auth.uid()),new.correction_reason,old.payload,new.payload);
 new.updated_at=now(); new.correction_reason=null; return new;
end $$;
create trigger measurement_audit before update on public.walk_measurements
for each row execute function app_private.measurement_audit_guard();
revoke all on function app_private.measurement_audit_guard() from public,anon,authenticated;
revoke all on function app_private.field_record_immutable_guard() from public,anon,authenticated;
