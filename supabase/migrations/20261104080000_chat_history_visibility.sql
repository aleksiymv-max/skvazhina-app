-- Per-user conversation deletion is a visibility tombstone, not a global data purge.
alter table public.promysel_chat_members
 add column if not exists visible_since timestamptz not null default 'epoch'::timestamptz;
-- Honor pre-existing hidden chats that were removed before this upgrade.
update public.promysel_chat_members set visible_since=now()
 where hidden=true and visible_since='epoch'::timestamptz;
create index if not exists promysel_chat_member_visible_since_idx
 on public.promysel_chat_members(user_id,room_id,visible_since);
create or replace function public.promysel_chat_listing(p_user uuid,p_field text)
returns jsonb language sql stable security invoker set search_path=''
as $$
 select coalesce(jsonb_agg(
  jsonb_build_object(
   'id',r.id,'field_id',r.field_id,'kind',r.kind,'title',r.title,
   'avatar_path',r.avatar_path,'created_by',r.created_by,'created_at',r.created_at,
   'updated_at',r.updated_at,'muted',own.muted,'soundEnabled',own.sound_enabled,
   'pinned',own.pinned,'lastReadAt',own.last_read_at,'visibleSince',own.visible_since,'people',coalesce(people.data,'[]'::jsonb),
   'last',case when lastmsg.id is null then null else
      jsonb_build_object('id',lastmsg.id,'body',case when lastmsg.deleted_at is null then lastmsg.body else '' end,
        'kind',lastmsg.kind,'created_at',lastmsg.created_at,
        'sender_id',lastmsg.sender_id,'deleted_at',lastmsg.deleted_at) end,
   'unread',coalesce(unread.total,0)) order by own.pinned desc,r.updated_at desc),
   '[]'::jsonb)
 from public.promysel_chat_members own
 join public.promysel_chat_rooms r on r.id=own.room_id
 left join lateral (
  select jsonb_agg(jsonb_build_object('id',m.user_id,
     'name',coalesce(fm.display_name,'Сотрудник'),
     'readAt',m.last_read_at) order by m.joined_at) as data
  from public.promysel_chat_members m
  left join public.field_memberships fm
     on fm.user_id=m.user_id and fm.field_id=r.field_id
  where m.room_id=r.id
 ) people on true
 left join lateral (
  select msg.id,msg.body,msg.kind,msg.created_at,msg.sender_id,msg.deleted_at
  from public.promysel_chat_messages msg
  where msg.room_id=r.id and msg.created_at>=own.visible_since order by msg.created_at desc limit 1
 ) lastmsg on true
 left join lateral (
  select count(*) as total from public.promysel_chat_messages msg
  where msg.room_id=r.id and msg.created_at>own.last_read_at and msg.created_at>=own.visible_since
     and msg.sender_id<>p_user and msg.deleted_at is null
 ) unread on true
 where own.user_id=p_user and own.hidden=false and r.field_id=p_field
  and (r.kind='group' or lastmsg.id is not null)
  and exists (select 1 from public.field_memberships fm
    join public.oil_fields f on f.id=fm.field_id and f.archived_at is null
    where fm.field_id=r.field_id and fm.user_id=p_user
      and fm.approved=true and fm.blocked=false);
$$;
revoke all on function public.promysel_chat_listing(uuid,text)
 from public, anon, authenticated;
grant execute on function public.promysel_chat_listing(uuid,text) to service_role;
