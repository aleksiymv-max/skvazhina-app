-- v2.06.2: 384px PNG avatars may be larger than 240 KiB after Base64.
-- The Edge endpoint still enforces a hard <1MiB request body limit.
begin;
alter table public.promysel_avatar_versions
  drop constraint if exists promysel_avatar_value_size;
alter table public.promysel_avatar_versions
  add constraint promysel_avatar_value_size
  check(length(avatar_value)<=900000);
create or replace function public.promysel_avatar_commit_v206(
 p_field_id text,p_user_id uuid,p_avatar text,
 p_expected_revision bigint,p_operation_id text
) returns jsonb language plpgsql security definer set search_path='' as $fn$
declare existing public.promysel_avatar_versions%rowtype;
 v_rev bigint;
begin
 if p_field_id is null or p_user_id is null or
    length(p_operation_id) not between 8 and 120 or
    p_operation_id !~ '^[A-Za-z0-9:_-]+$' or
    p_expected_revision is null or p_expected_revision<0 then
   raise exception 'Некорректные параметры изменения фотографии';
 end if;
 if not exists (select 1 from public.field_memberships m
   where m.field_id=p_field_id and m.user_id=p_user_id
     and m.approved and not m.blocked)
 then raise exception 'Нет допуска сотрудника к месторождению';end if;
 if p_avatar is null then p_avatar:='__deleted__';end if;
 if p_avatar<>'__deleted__' and
   (length(p_avatar) not between 24 and 900000 or
    p_avatar !~ '^[A-Za-z0-9+/=]+$')
 then raise exception 'Некорректное изображение';end if;
 select * into existing from public.promysel_avatar_versions v
   where v.field_id=p_field_id and v.user_id=p_user_id for update;
 if found then
   if existing.last_mutation_id=p_operation_id then
     return jsonb_build_object('status','already_applied','revision',existing.revision);
   end if;
   if existing.revision<>p_expected_revision then
     return jsonb_build_object('status','conflict','revision',existing.revision);
   end if;
   update public.promysel_avatar_versions
   set avatar_value=p_avatar,revision=existing.revision+1,
     last_mutation_id=p_operation_id,updated_at=now()
   where field_id=p_field_id and user_id=p_user_id
   returning revision into v_rev;
 else
   if p_expected_revision<>0 then
     return jsonb_build_object('status','conflict','revision',0);
   end if;
   insert into public.promysel_avatar_versions(
     field_id,user_id,avatar_value,revision,last_mutation_id)
   values(p_field_id,p_user_id,p_avatar,1,p_operation_id)
   returning revision into v_rev;
 end if;
 return jsonb_build_object('status','ok','revision',v_rev);
end $fn$;
revoke all on function public.promysel_avatar_commit_v206(text,uuid,text,bigint,text)
 from public,anon,authenticated;
grant execute on function public.promysel_avatar_commit_v206(text,uuid,text,bigint,text)
 to service_role;
commit;
