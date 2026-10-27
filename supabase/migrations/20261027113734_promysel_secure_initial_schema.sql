
-- Promysel cloud foundation. No production data is deleted or imported.
create schema if not exists app_private;
revoke all on schema app_private from public, anon;
grant usage on schema app_private to authenticated;

create table public.oil_fields (
 id text primary key check (length(trim(id)) between 1 and 128),
 name text not null check (length(trim(name)) between 1 and 200),
 created_at timestamptz not null default now()
);
create table public.field_memberships (
 user_id uuid not null references auth.users(id) on delete cascade,
 field_id text not null references public.oil_fields(id) on delete cascade,
 display_name text not null default '',
 role text not null check (role in ('admin','shopChief','engineer','dispatcher','manager','operator')),
 subrole text check (subrole is null or subrole in ('leadingGeologist','leadingTechnologist','geologist','technologist','master','dispatcher')),
 approved boolean not null default false,
 blocked boolean not null default false,
 joined_at timestamptz not null default now(),
 primary key (user_id, field_id)
);
create index field_memberships_field_idx on public.field_memberships(field_id) where approved and not blocked;

-- Evaluated against the verified Supabase Auth user; never trust user_metadata.
-- The function owner can read memberships without recursing through their RLS policy.
create function app_private.member_role(p_field text) returns text
language sql stable security definer set search_path = ''
as $$
  select m.role from public.field_memberships m
  where m.user_id = (select auth.uid()) and m.field_id = p_field
    and m.approved and not m.blocked
  limit 1
$$;
create function app_private.is_member(p_field text) returns boolean
language sql stable security definer set search_path = ''
as $$ select app_private.member_role(p_field) is not null $$;
create function app_private.can_structure(p_field text) returns boolean
language sql stable security definer set search_path = ''
as $$ select app_private.member_role(p_field) in ('admin','shopChief','engineer') $$;
create function app_private.can_delete_structure(p_field text) returns boolean
language sql stable security definer set search_path = ''
as $$ select app_private.member_role(p_field) in ('admin','shopChief') $$;
create function app_private.can_walk(p_field text) returns boolean
language sql stable security definer set search_path = ''
as $$ select app_private.member_role(p_field) in ('shopChief','engineer','operator') $$;
create function app_private.can_correct(p_field text) returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (
    select 1 from public.field_memberships m
    where m.user_id=(select auth.uid()) and m.field_id=p_field
      and m.approved and not m.blocked
      and (m.role='shopChief' or (m.role='engineer' and coalesce(m.subrole,'') <> 'master'))
  )
$$;
revoke all on all functions in schema app_private from public, anon;
grant execute on all functions in schema app_private to authenticated;

create table public.production_areas (
 id text primary key, field_id text not null references public.oil_fields(id) on delete restrict,
 name text not null, config jsonb not null default '{}'::jsonb,
 updated_at timestamptz not null default now(),
 unique (field_id,id)
);
create table public.pads (
 id text primary key, field_id text not null references public.oil_fields(id) on delete restrict,
 area_id text, name text not null, kind text not null default 'oil',
 config jsonb not null default '{}'::jsonb, updated_at timestamptz not null default now(),
 unique(field_id,id),
 foreign key(field_id,area_id) references public.production_areas(field_id,id) on delete set null (area_id)
);
create table public.wells (
 id text primary key, field_id text not null references public.oil_fields(id) on delete restrict,
 pad_id text not null, well_number text not null,
 well_type text not null default 'oil', status text,
 config jsonb not null default '{}'::jsonb, updated_at timestamptz not null default now(),
 unique(field_id,id),
 foreign key(field_id,pad_id) references public.pads(field_id,id) on delete restrict
);
create index wells_pad_idx on public.wells(field_id,pad_id);

-- Immutable historical snapshots: changing today's parameter layout must not rewrite old walks.
create table public.walk_measurements (
 id text primary key,
 field_id text not null references public.oil_fields(id) on delete restrict,
 pad_id text not null, well_id text not null,
 measured_at timestamptz not null,
 payload jsonb not null,
 actor_id uuid not null references auth.users(id),
 created_at timestamptz not null default now(),
 updated_at timestamptz not null default now(),
 foreign key(field_id,pad_id) references public.pads(field_id,id) on delete restrict,
 foreign key(field_id,well_id) references public.wells(field_id,id) on delete restrict
);
create index walk_measurements_well_time_idx on public.walk_measurements(field_id,well_id,measured_at desc);
create table public.measurement_corrections (
 id bigint generated always as identity primary key,
 measurement_id text not null references public.walk_measurements(id) on delete restrict,
 field_id text not null references public.oil_fields(id) on delete restrict,
 actor_id uuid not null references auth.users(id),
 corrected_at timestamptz not null default now(),
 reason text not null check (length(trim(reason)) between 1 and 2000),
 before_payload jsonb not null,
 after_payload jsonb not null
);

-- Separate changeable records instead of giving an operator unrestricted access to the whole field snapshot.
create table public.field_records (
 id text primary key,
 field_id text not null references public.oil_fields(id) on delete restrict,
 kind text not null check (kind in ('task','problem','annulus_pressure','training','notification','equipment','repair')),
 well_id text, owner_id uuid references auth.users(id),
 payload jsonb not null default '{}'::jsonb,
 created_by uuid not null references auth.users(id),
 updated_at timestamptz not null default now(),
 foreign key(field_id,well_id) references public.wells(field_id,id) on delete restrict
);
create index field_records_field_kind_idx on public.field_records(field_id,kind,updated_at desc);

-- Cloud delta log. Unique client idempotency keys prevent duplicate records on retries.
create table public.sync_events (
 sequence bigint generated always as identity primary key,
 event_key text not null unique check (length(event_key) between 1 and 300),
 field_id text not null references public.oil_fields(id) on delete restrict,
 device_id text not null check (length(device_id) between 1 and 200),
 event_type text not null check (event_type in ('measurement','task','problem','annulus_pressure','training','notification','equipment','repair')),
 payload jsonb not null,
 actor_id uuid not null references auth.users(id),
 client_updated_at timestamptz,
 server_received_at timestamptz not null default now()
);
create index sync_events_pull_idx on public.sync_events(field_id,sequence);

create table public.registration_requests (
 id bigint generated always as identity primary key,
 requested_by uuid not null references auth.users(id),
 field_id text references public.oil_fields(id) on delete restrict,
 proposed_field_name text,
 requested_role text not null check (requested_role in ('shopChief','engineer','dispatcher','operator')),
 requested_subrole text,
 full_name text not null,
 email text not null,
 state text not null default 'pending' check(state in('pending','approved','rejected')),
 created_at timestamptz not null default now(),
 decided_by uuid references auth.users(id),
 decided_at timestamptz,
 check ((field_id is not null) <> (proposed_field_name is not null))
);

-- Deny by default. Public Data API needs explicit grants AND row policies.
alter table public.oil_fields enable row level security;
alter table public.field_memberships enable row level security;
alter table public.production_areas enable row level security;
alter table public.pads enable row level security;
alter table public.wells enable row level security;
alter table public.walk_measurements enable row level security;
alter table public.measurement_corrections enable row level security;
alter table public.field_records enable row level security;
alter table public.sync_events enable row level security;
alter table public.registration_requests enable row level security;
revoke all on public.oil_fields,public.field_memberships,public.production_areas,public.pads,public.wells,public.walk_measurements,public.measurement_corrections,public.field_records,public.sync_events,public.registration_requests from anon;
revoke all on public.oil_fields,public.field_memberships,public.production_areas,public.pads,public.wells,public.walk_measurements,public.measurement_corrections,public.field_records,public.sync_events,public.registration_requests from authenticated;
grant select on public.oil_fields,public.field_memberships,public.production_areas,public.pads,public.wells,public.walk_measurements,public.measurement_corrections,public.field_records,public.sync_events,public.registration_requests to authenticated;
grant insert on public.walk_measurements,public.measurement_corrections,public.field_records,public.sync_events,public.registration_requests to authenticated;
grant insert,update on public.production_areas,public.pads,public.wells to authenticated;
grant update on public.walk_measurements,public.field_records to authenticated;
grant delete on public.production_areas,public.pads,public.wells to authenticated;
grant usage,select on all sequences in schema public to authenticated;

create policy field_select on public.oil_fields for select to authenticated
 using (app_private.is_member(id));
create policy membership_select on public.field_memberships for select to authenticated
 using (user_id=(select auth.uid()) or app_private.can_delete_structure(field_id));
create policy area_select on public.production_areas for select to authenticated
 using (app_private.is_member(field_id));
create policy area_create on public.production_areas for insert to authenticated
 with check (app_private.can_structure(field_id));
create policy area_modify on public.production_areas for update to authenticated
 using (app_private.can_structure(field_id)) with check(app_private.can_structure(field_id));
create policy area_remove on public.production_areas for delete to authenticated
 using (app_private.can_delete_structure(field_id));
create policy pad_select on public.pads for select to authenticated
 using (app_private.is_member(field_id));
create policy pad_create on public.pads for insert to authenticated
 with check (app_private.can_structure(field_id));
create policy pad_modify on public.pads for update to authenticated
 using (app_private.can_structure(field_id)) with check(app_private.can_structure(field_id));
create policy pad_remove on public.pads for delete to authenticated
 using (app_private.can_delete_structure(field_id));
create policy well_select on public.wells for select to authenticated
 using (app_private.is_member(field_id));
create policy well_create on public.wells for insert to authenticated
 with check (app_private.can_structure(field_id));
create policy well_modify on public.wells for update to authenticated
 using (app_private.can_structure(field_id)) with check(app_private.can_structure(field_id));
create policy well_remove on public.wells for delete to authenticated
 using (app_private.can_delete_structure(field_id));
create policy walk_select on public.walk_measurements for select to authenticated
 using (app_private.is_member(field_id));
create policy walk_insert on public.walk_measurements for insert to authenticated
 with check (actor_id=(select auth.uid()) and app_private.can_walk(field_id));
create policy walk_correct on public.walk_measurements for update to authenticated
 using (app_private.can_correct(field_id)) with check(app_private.can_correct(field_id));
create policy correction_select on public.measurement_corrections for select to authenticated
 using (app_private.is_member(field_id));
create policy correction_insert on public.measurement_corrections for insert to authenticated
 with check(actor_id=(select auth.uid()) and app_private.can_correct(field_id));
create policy records_select on public.field_records for select to authenticated
 using (app_private.is_member(field_id));
create policy records_insert on public.field_records for insert to authenticated
 with check (created_by=(select auth.uid()) and app_private.is_member(field_id) and
   (kind<>'training' or owner_id=(select auth.uid())));
create policy records_update on public.field_records for update to authenticated
 using (app_private.is_member(field_id) and (created_by=(select auth.uid()) or app_private.can_correct(field_id)))
 with check (app_private.is_member(field_id) and (created_by=(select auth.uid()) or app_private.can_correct(field_id)));
create policy sync_select on public.sync_events for select to authenticated
 using (app_private.is_member(field_id));
create policy sync_insert on public.sync_events for insert to authenticated
 with check (actor_id=(select auth.uid()) and app_private.is_member(field_id)
    and (event_type <> 'measurement' or app_private.can_walk(field_id)));
create policy registration_select on public.registration_requests for select to authenticated
 using (requested_by=(select auth.uid()) or (field_id is not null and app_private.can_delete_structure(field_id)));
create policy registration_insert on public.registration_requests for insert to authenticated
 with check (requested_by=(select auth.uid()) and state='pending' and decided_at is null and decided_by is null);
