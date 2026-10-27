
-- Keep event-sourced full-field snapshots limited to elevated structure roles.
alter table public.sync_events drop constraint sync_events_event_type_check;
alter table public.sync_events add constraint sync_events_event_type_check
  check (event_type in ('measurement','app_state','task','problem','annulus_pressure','training','notification','equipment','repair'));
drop policy sync_insert on public.sync_events;
create policy sync_insert on public.sync_events for insert to authenticated
 with check (
 actor_id=(select auth.uid()) and app_private.is_member(field_id)
 and (event_type <> 'measurement' or app_private.can_walk(field_id))
 and (event_type <> 'app_state' or app_private.can_structure(field_id))
 );
-- Supabase's existing RLS trigger is not intended to be directly callable via REST.
revoke all on function public.rls_auto_enable() from public,anon,authenticated;
-- Foreign-key covering indexes for deletion/update and reporting.
create index if not exists field_records_created_by_idx on public.field_records(created_by);
create index if not exists field_records_owner_idx on public.field_records(owner_id);
create index if not exists field_records_field_well_idx on public.field_records(field_id,well_id);
create index if not exists corrections_actor_idx on public.measurement_corrections(actor_id);
create index if not exists corrections_field_idx on public.measurement_corrections(field_id);
create index if not exists corrections_measurement_idx on public.measurement_corrections(measurement_id);
create index if not exists pads_area_idx on public.pads(field_id,area_id);
create index if not exists registration_decider_idx on public.registration_requests(decided_by);
create index if not exists registration_field_idx on public.registration_requests(field_id);
create index if not exists registration_requester_idx on public.registration_requests(requested_by);
create index if not exists sync_events_actor_idx on public.sync_events(actor_id);
create index if not exists walk_actor_idx on public.walk_measurements(actor_id);
create index if not exists walk_pad_idx on public.walk_measurements(field_id,pad_id);
