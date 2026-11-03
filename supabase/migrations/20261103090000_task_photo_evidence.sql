-- Private task photo evidence, independent of legacy app_state task status.
-- No existing tasks or measurements are modified or deleted by this migration.
create table if not exists public.promysel_task_photo_registry (
  field_id text not null references public.oil_fields(id) on delete cascade,
  task_id text not null check(length(task_id) between 1 and 128),
  created_by uuid not null,
  target_type text not null check(target_type in ('personal','area','pad')),
  target_id text not null check(length(target_id) between 1 and 128),
  created_at timestamptz not null default now(),
  primary key(field_id,task_id)
);
create index if not exists promysel_task_photo_registry_creator
 on public.promysel_task_photo_registry(created_by,field_id);
alter table public.promysel_task_photo_registry enable row level security;
revoke all on public.promysel_task_photo_registry from anon,authenticated;

create table if not exists public.promysel_task_photos (
  id uuid primary key default gen_random_uuid(),
  field_id text not null,
  task_id text not null,
  phase text not null check (phase in ('assignment','completion')),
  uploaded_by uuid not null,
  client_upload_id uuid not null,
  original_name text not null check(length(original_name) between 1 and 180),
  content_type text not null check(content_type in ('image/jpeg','image/png','image/webp')),
  object_path text not null unique,
  uploaded_at timestamptz not null default now(),
  foreign key(field_id,task_id)
    references public.promysel_task_photo_registry(field_id,task_id)
    on delete cascade,
  unique(field_id,task_id,uploaded_by,client_upload_id)
);
create index if not exists promysel_task_photos_by_task
  on public.promysel_task_photos(field_id,task_id,uploaded_at desc);
alter table public.promysel_task_photos enable row level security;
revoke all on public.promysel_task_photos from anon,authenticated;

-- Storage is accessible only from the authenticated, scoped Edge Function.
insert into storage.buckets(id,name,public,file_size_limit,allowed_mime_types)
 values('promysel-task-photos','promysel-task-photos',false,5242880,
 array['image/jpeg','image/png','image/webp'])
 on conflict (id) do nothing;
-- There are deliberately no public/authenticated storage.objects policies for this bucket.
-- Service role requests are filtered by verified field membership and task ownership.
