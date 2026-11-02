-- Isolated PostgreSQL fixture. Synthetic users and fields only.
-- Run in a throwaway PostgreSQL service, NEVER on the production database.
create role anon nologin;
create role authenticated nologin;
create role service_role nologin;
create schema auth;
create schema app_private;
create schema storage;
create function auth.uid() returns uuid language sql stable
as $$ select nullif(current_setting('request.jwt.claim.sub',true),'')::uuid $$;
create table auth.users(id uuid primary key);
create table public.oil_fields(id text primary key);
create table public.field_memberships(
  user_id uuid not null references auth.users(id),
  field_id text not null references public.oil_fields(id),
  role text not null, approved boolean not null, blocked boolean not null,
  primary key(user_id,field_id)
);
create table public.production_areas(id text primary key,field_id text not null references public.oil_fields(id));
create table public.pads(id text primary key,field_id text not null references public.oil_fields(id));
create table storage.buckets(
  id text primary key,name text not null,public boolean not null,
  file_size_limit bigint,allowed_mime_types text[]
);
create table storage.objects(
  id bigint generated always as identity primary key,
  bucket_id text not null references storage.buckets(id),
  name text not null
);
alter table storage.objects enable row level security;
grant usage on schema auth,app_private,storage to authenticated;
grant select on public.field_memberships,public.production_areas,public.pads to authenticated;
grant select,insert on storage.objects to authenticated;
create function app_private.member_role(p_field text) returns text
language sql stable security definer set search_path='' as $$
  select m.role from public.field_memberships m
  where m.user_id=(select auth.uid()) and m.field_id=p_field
    and m.approved and not m.blocked limit 1
$$;
create function app_private.is_member(p_field text) returns boolean
language sql stable security definer set search_path='' as $$
  select app_private.member_role(p_field) is not null
$$;
create function app_private.can_walk(p_field text) returns boolean
language sql stable security definer set search_path='' as $$
  select app_private.member_role(p_field) in ('shopChief','engineer','operator')
$$;
create function app_private.can_manage_tasks(p_field text) returns boolean
language sql stable security definer set search_path='' as $$
  select app_private.member_role(p_field) in ('shopChief','admin','engineer')
$$;
insert into auth.users(id) values
('00000000-0000-0000-0000-000000000001'),
('00000000-0000-0000-0000-000000000002'),
('00000000-0000-0000-0000-000000000003'),
('00000000-0000-0000-0000-000000000004'),
('00000000-0000-0000-0000-000000000005');
insert into public.oil_fields(id) values('field-a'),('field-b');
insert into public.production_areas(id,field_id) values('area-a','field-a');
insert into public.pads(id,field_id) values('pad-a','field-a');
insert into public.field_memberships(user_id,field_id,role,approved,blocked) values
('00000000-0000-0000-0000-000000000001','field-a','shopChief',true,false),
('00000000-0000-0000-0000-000000000002','field-a','operator',true,false),
('00000000-0000-0000-0000-000000000003','field-a','operator',true,false),
('00000000-0000-0000-0000-000000000004','field-a','operator',true,true),
('00000000-0000-0000-0000-000000000005','field-b','operator',true,false);
