-- v2.04.1 production hotfix: outbound sync/push fails with SQLSTATE 42702.
-- The earlier trigger compared s.task_id = task_id, but 'task_id' is BOTH
-- a PL/pgSQL variable and a table column; PostgreSQL raises ambiguous_column.
-- Rename all function variables with v_ prefix, qualify every SQL identifier.
-- No deletions, RLS changes, or modifications of existing task history.
create or replace function app_private.promysel_guard_task_field_v204()
returns trigger
language plpgsql
security definer
set search_path=''
as $function$
declare
  v_item jsonb;
  v_retained jsonb:='[]'::jsonb;
  v_task_id text;
  v_task_field text;
  v_owner_field text;
  v_creator text;
begin
  if new.event_type<>'app_state'
     or jsonb_typeof(new.payload->'tasks')<>'array' then
    return new;
  end if;
  for v_item in
    select j.value from jsonb_array_elements(new.payload->'tasks') as j(value)
  loop
    v_task_id:=v_item->>'id';
    v_task_field:=v_item->>'fieldId';
    v_creator:=v_item->>'createdById';
    v_owner_field:=null;
    if v_task_id is null or length(v_task_id) not between 1 and 180 then
      continue;
    end if;
    if v_task_field is not null and v_task_field<>new.field_id then
      continue;
    end if;
    select sc.field_id into v_owner_field
      from public.promysel_task_scopes as sc
      where sc.task_id=v_task_id;
    if v_owner_field is null then
      if v_task_field is null and not exists (
        select 1 from public.field_memberships as member
        where member.field_id=new.field_id
          and member.user_id::text=v_creator
          and member.approved and not member.blocked
      ) then
        continue;
      end if;
      insert into public.promysel_task_scopes(task_id,field_id,scope_source)
      values(
        v_task_id,new.field_id,
        case when v_task_field is null
          then 'verified-creator-legacy-client'
          else 'explicit-client-field' end
      ) on conflict(task_id) do nothing;
      select sc.field_id into v_owner_field
        from public.promysel_task_scopes as sc
        where sc.task_id=v_task_id;
    end if;
    if v_owner_field=new.field_id then
      v_retained:=v_retained||jsonb_build_array(
        v_item||jsonb_build_object('fieldId',new.field_id)
      );
    end if;
  end loop;
  new.payload:=jsonb_set(new.payload,'{tasks}',v_retained,true);
  return new;
exception when others then
  raise exception 'Невозможно проверить принадлежность заданий месторождению (SQLSTATE %)',sqlstate;
end
$function$;
