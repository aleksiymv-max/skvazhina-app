create table if not exists public.promysel_daily_presence (
 field_id text not null references public.oil_fields(id) on delete restrict,
 user_id uuid not null references auth.users(id) on delete restrict,
 work_day date not null,
 is_working boolean not null,
 changed_by uuid not null references auth.users(id) on delete restrict,
 updated_at timestamptz not null default now(),
 primary key(field_id,user_id,work_day)
);
create index if not exists promysel_presence_day_idx on public.promysel_daily_presence(field_id,work_day);
alter table public.promysel_daily_presence enable row level security;
revoke all on public.promysel_daily_presence from public,anon,authenticated;
grant select,insert,update,delete on public.promysel_daily_presence to service_role;
