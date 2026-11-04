-- Safe and idempotent: activated in Supabase before the Web/APK release.
-- Only the service role can call this authorization helper.
create or replace function public.promysel_chat_room_scope(p_user uuid,p_room uuid)
returns jsonb language sql stable security invoker set search_path='' as $$
 select jsonb_build_object('room',to_jsonb(r),'member',to_jsonb(cm))
 from public.promysel_chat_rooms r
 join public.promysel_chat_members cm on cm.room_id=r.id and cm.user_id=p_user
 join public.field_memberships fm on fm.user_id=p_user and fm.field_id=r.field_id
   and fm.approved=true and fm.blocked=false
 join public.oil_fields f on f.id=r.field_id and f.archived_at is null
 where r.id=p_room
 limit 1
$$;
revoke all on function public.promysel_chat_room_scope(uuid,uuid) from public,anon,authenticated;
grant execute on function public.promysel_chat_room_scope(uuid,uuid) to service_role;
create index if not exists promysel_chat_rooms_created_by_idx on public.promysel_chat_rooms(created_by);
create index if not exists promysel_chat_messages_live_room_time_idx on public.promysel_chat_messages(room_id,created_at desc) where deleted_at is null;
