-- Messaging is isolated from production well/history tables. Private Storage is served only via authenticated Edge APIs.
create table if not exists public.promysel_chat_rooms (
 id uuid primary key default gen_random_uuid(),
 field_id text not null references public.oil_fields(id) on delete restrict,
 kind text not null check (kind in ('private','group','saved')),
 title text not null default '',
 pair_key text unique,
 avatar_path text,
 created_by uuid not null references auth.users(id) on delete restrict,
 created_at timestamptz not null default now(),
 updated_at timestamptz not null default now()
);
create index if not exists promysel_chat_rooms_field_idx on public.promysel_chat_rooms(field_id,updated_at desc);
create table if not exists public.promysel_chat_members (
 room_id uuid not null references public.promysel_chat_rooms(id) on delete cascade,
 user_id uuid not null references auth.users(id) on delete restrict,
 muted boolean not null default false,
 sound_enabled boolean not null default true,
 last_read_at timestamptz not null default 'epoch'::timestamptz,
 joined_at timestamptz not null default now(),
 primary key(room_id,user_id)
);
create index if not exists promysel_chat_members_user_idx on public.promysel_chat_members(user_id,room_id);
create table if not exists public.promysel_chat_messages (
 id uuid primary key default gen_random_uuid(),
 room_id uuid not null references public.promysel_chat_rooms(id) on delete cascade,
 sender_id uuid not null references auth.users(id) on delete restrict,
 body text not null default '',
 kind text not null default 'text' check (kind in ('text','image','video','voice','document')),
 attachment_path text,
 attachment_name text,
 mime_type text,
 bytes bigint,
 created_at timestamptz not null default now(),
 edited_at timestamptz,
 deleted_at timestamptz,
 client_id uuid,
 unique(room_id,sender_id,client_id),
 check (length(body) <= 8000),
 check ((kind='text' and length(trim(body))>0) or (kind<>'text' and attachment_path is not null))
);
create index if not exists promysel_chat_messages_room_idx on public.promysel_chat_messages(room_id,created_at desc);
create index if not exists promysel_chat_messages_sender_idx on public.promysel_chat_messages(sender_id);

alter table public.promysel_chat_rooms enable row level security;
alter table public.promysel_chat_members enable row level security;
alter table public.promysel_chat_messages enable row level security;
revoke all on public.promysel_chat_rooms, public.promysel_chat_members, public.promysel_chat_messages from anon,authenticated;
revoke all on public.promysel_chat_rooms, public.promysel_chat_members, public.promysel_chat_messages from public;

insert into storage.buckets(id,name,public,file_size_limit,allowed_mime_types)
values ('promysel-chat','promysel-chat',false,52428800,null)
on conflict(id) do update set public=false,file_size_limit=52428800;
-- No client storage policies: server validates JWT, room membership and file ownership before signed URLs.