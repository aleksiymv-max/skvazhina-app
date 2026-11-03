-- Atomic loss-resistant merge of legacy state snapshots. No production rows are deleted.
create or replace function app_private.promysel_merge_state_rows(previous jsonb,incoming jsonb,key_kind text default 'id')
returns jsonb language plpgsql immutable set search_path='' as $$
declare result_rows jsonb:=case when jsonb_typeof(previous)='array' then previous else '[]'::jsonb end;
 input_rows jsonb:=case when jsonb_typeof(incoming)='array' then incoming else '[]'::jsonb end;
 item jsonb;old_item jsonb;match_at integer;idx integer;id_key text;old_key text;
begin
 for item in select value from pg_catalog.jsonb_array_elements(input_rows) loop
  if pg_catalog.jsonb_typeof(item)<>'object' then continue;end if;
  if key_kind='annulus' then id_key:=coalesce(item->>'wellId','')||'|'||coalesce(item->>'date','');
  else id_key:=coalesce(item->>'id','');end if;
  match_at:=null;
  if id_key<>'' and id_key<>'|' then
    for idx in 0..pg_catalog.jsonb_array_length(result_rows)-1 loop
      old_item:=result_rows->idx;
      if key_kind='annulus' then old_key:=coalesce(old_item->>'wellId','')||'|'||coalesce(old_item->>'date','');
      else old_key:=coalesce(old_item->>'id','');end if;
      if id_key=old_key then match_at:=idx;exit;end if;
    end loop;
  end if;
  if match_at is null then
    if not result_rows @> pg_catalog.jsonb_build_array(item) then result_rows:=result_rows||pg_catalog.jsonb_build_array(item);end if;
  else
    old_item:=result_rows->match_at;
    if key_kind='pads' then item:=pg_catalog.jsonb_set(old_item||item,'{wells}',app_private.promysel_merge_state_rows(old_item->'wells',item->'wells','id'),true);
    elsif key_kind='tasks' then
      if old_item->>'status'='confirmed' and item->>'status'<>'confirmed' then item:=old_item;
      elsif old_item->>'status'='awaitingConfirmation' and item->>'status'='active' and coalesce(item->>'rejectedAt','')='' then item:=old_item;
      elsif coalesce(old_item->>'rejectedAt','')<>'' and item->>'status'='awaitingConfirmation'
        and coalesce(item->>'completedAt','')<=coalesce(old_item->>'rejectedAt','') then item:=old_item;
      else item:=old_item||item;end if;
    elsif key_kind='notifications' and old_item->>'read'='true' then item:=(old_item||item)||'{"read":true}'::jsonb;
    else item:=old_item||item;end if;
    result_rows:=pg_catalog.jsonb_set(result_rows,array[match_at::text],item,true);
  end if;
 end loop;
 return result_rows;
end $$;

create or replace function app_private.promysel_merge_state_snapshots(previous jsonb,incoming jsonb)
returns jsonb language plpgsql immutable set search_path='' as $$
declare result jsonb;name text;old_cfg jsonb;new_cfg jsonb;merged_cfg jsonb;cfg_key text;
begin
 if pg_catalog.jsonb_typeof(incoming)<>'object' then raise exception 'Invalid app_state payload';end if;
 if previous is null then return incoming;end if;
 result:=previous||incoming;
 foreach name in array array['areas','pads','tasks','training','notifications','annulus'] loop
  result:=pg_catalog.jsonb_set(result,array[name],
    app_private.promysel_merge_state_rows(previous->name,incoming->name,
      case when name='annulus' then 'annulus' else name end),true);
 end loop;
 foreach name in array array['problemApplications','avatars'] loop
   if pg_catalog.jsonb_typeof(previous->name)='object' or pg_catalog.jsonb_typeof(incoming->name)='object' then
    result:=pg_catalog.jsonb_set(result,array[name],
      (case when pg_catalog.jsonb_typeof(previous->name)='object' then previous->name else '{}'::jsonb end)
      ||(case when pg_catalog.jsonb_typeof(incoming->name)='object' then incoming->name else '{}'::jsonb end),true);
   end if;
 end loop;
 old_cfg:=case when pg_catalog.jsonb_typeof(previous->'walkConfig')='object' then previous->'walkConfig' else '{}'::jsonb end;
 new_cfg:=case when pg_catalog.jsonb_typeof(incoming->'walkConfig')='object' then incoming->'walkConfig' else '{}'::jsonb end;
 merged_cfg:=old_cfg||new_cfg;
 foreach cfg_key in array array['enabled','units','wellEnabled','wellUnits'] loop
   merged_cfg:=pg_catalog.jsonb_set(merged_cfg,array[cfg_key],
      (case when pg_catalog.jsonb_typeof(old_cfg->cfg_key)='object' then old_cfg->cfg_key else '{}'::jsonb end)
      ||(case when pg_catalog.jsonb_typeof(new_cfg->cfg_key)='object' then new_cfg->cfg_key else '{}'::jsonb end),true);
 end loop;
 return pg_catalog.jsonb_set(result,'{walkConfig}',merged_cfg,true);
end $$;

create or replace function app_private.promysel_reconcile_state_event()
returns trigger language plpgsql security definer set search_path='' as $$
declare prior jsonb;
begin
 if new.event_type<>'app_state' then return new;end if;
 if new.payload->>'fieldId' is distinct from new.field_id then raise exception 'app_state field mismatch';end if;
 perform pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended(new.field_id,410267));
 select e.payload into prior from public.sync_events e where e.field_id=new.field_id
   and e.event_type='app_state' order by e.sequence desc limit 1;
 if prior is not null then new.payload:=app_private.promysel_merge_state_snapshots(prior,new.payload);end if;
 return new;
end $$;
drop trigger if exists promysel_reconcile_state_insert on public.sync_events;
create trigger promysel_reconcile_state_insert before insert on public.sync_events
 for each row when (new.event_type='app_state')
 execute function app_private.promysel_reconcile_state_event();
revoke all on function app_private.promysel_merge_state_rows(jsonb,jsonb,text) from public,anon,authenticated;
revoke all on function app_private.promysel_merge_state_snapshots(jsonb,jsonb) from public,anon,authenticated;
revoke all on function app_private.promysel_reconcile_state_event() from public,anon,authenticated;
