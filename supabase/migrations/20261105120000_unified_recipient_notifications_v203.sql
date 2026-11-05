-- v2.03 — recipient-bound, idempotent notification event pipeline.
-- Events belong to exactly one employee + one field. Only the service-role
-- Edge Function can read or acknowledge them. No legacy data is deleted.
begin;

alter table public.promysel_push_events
  add column if not exists category text not null default 'task',
  add column if not exists route text not null default '/tasks',
  add column if not exists read_at timestamptz,
  add column if not exists priority text not null default 'normal';
create index if not exists promysel_push_inbox_v203
  on public.promysel_push_events(user_id,field_id,id desc);
create index if not exists promysel_push_unsent_v203
  on public.promysel_push_events(field_id,id) where sent_at is null and send_attempts<5;
alter table public.promysel_push_events enable row level security;
alter table public.promysel_push_subscriptions enable row level security;
revoke all on public.promysel_push_events from anon, authenticated;
revoke all on public.promysel_push_subscriptions from anon, authenticated;

create or replace function app_private.promysel_notify_chat_v203()
returns trigger language plpgsql security definer set search_path='' as $fn$
declare fid text; room_kind text; title text; excerpt text;
begin
  if new.sender_id is null or new.deleted_at is not null then return new; end if;
  select r.field_id,r.kind into fid,room_kind
    from public.promysel_chat_rooms r where r.id=new.room_id;
  if fid is null or room_kind='saved' then return new; end if;
  if not exists(select 1 from public.field_memberships m
     where m.user_id=new.sender_id and m.field_id=fid and m.approved and not m.blocked)
     then return new; end if;
  title:=case when room_kind='group' then 'Сообщение в групповом чате' else 'Новое сообщение' end;
  excerpt:=case new.kind when 'voice' then 'Голосовое сообщение'
    when 'video_note' then 'Видеосообщение'
    when 'video' then 'Видео'
    when 'image' then 'Фотография'
    when 'album' then 'Фотографии'
    when 'document' then 'Документ'
    else left(coalesce(nullif(new.body,''),'Сообщение'),180) end;
  insert into public.promysel_push_events(field_id,user_id,event_key,task_id,title,body,category,route)
  select fid,p.user_id,'chat:'||new.id,new.room_id::text,title,excerpt,'chat',
    '/chat/'||new.room_id::text
  from public.promysel_chat_members p
  join public.field_memberships fm
    on fm.user_id=p.user_id and fm.field_id=fid
  where p.room_id=new.room_id and p.user_id<>new.sender_id
    and not p.muted and not p.hidden and p.visible_since<=new.created_at
    and fm.approved and not fm.blocked
  on conflict(user_id,event_key) do nothing;
  return new;
exception when others then
  raise warning 'promysel chat notification queued with error SQLSTATE %',sqlstate;
  return new;
end $fn$;
drop trigger if exists promysel_chat_notify_v203 on public.promysel_chat_messages;
create trigger promysel_chat_notify_v203 after insert on public.promysel_chat_messages
for each row execute function app_private.promysel_notify_chat_v203();

-- Add the rest of the task lifecycle. Legacy task-created/completed trigger
-- still exists. Unique (user_id,event_key) prevents duplicates.
create or replace function app_private.promysel_notify_app_state_v203()
returns trigger language plpgsql security definer set search_path='' as $fn$
declare old_state jsonb:='{}'::jsonb;
  t jsonb; prior jsonb; item jsonb; old_item jsonb; v jsonb;
  task_id text; user_ref text; issuer text; target text; typ text; current_state text; previous_state text;
  field text:=new.field_id; current_day date:=(now() at time zone 'Asia/Tomsk')::date;
begin
 if new.event_type<>'app_state' then return new; end if;
 select e.payload into old_state from public.sync_events e
  where e.field_id=new.field_id and e.event_type='app_state' and e.sequence<new.sequence
  order by e.sequence desc limit 1;
 old_state:=coalesce(old_state,'{}'::jsonb);

 if jsonb_typeof(new.payload->'tasks')='array' then
   for t in select value from jsonb_array_elements(new.payload->'tasks') loop
     task_id:=t->>'id';
     if task_id is null or length(task_id)>120 then continue; end if;
     select value into prior from jsonb_array_elements(
       case when jsonb_typeof(old_state->'tasks')='array' then old_state->'tasks' else '[]'::jsonb end)
       where value->>'id'=task_id limit 1;
     issuer:=t->>'createdById'; target:=t->>'targetId';
     typ:=t->>'targetType'; current_state:=coalesce(t->>'status','');
     previous_state:=coalesce(prior->>'status','');
     if prior is null and current_state='active' then
       -- Personal assignments must reach the employee even outside their shift.
       -- Common assignments remain shift-scoped.
       if typ='personal' and target ~* '^[0-9a-f-]{36}$' then
         insert into public.promysel_push_events(field_id,user_id,event_key,task_id,title,body,category,route)
         select field,m.user_id,'task-created:'||task_id,task_id,
           'Новое личное задание',left(coalesce(t->>'title','Задание'),180),'task','/tasks'
         from public.field_memberships m
         where m.field_id=field and m.user_id=target::uuid and m.approved and not m.blocked
         on conflict(user_id,event_key) do nothing;
       end if;
     end if;
     if prior is not null and current_state<>previous_state then
       if current_state='rejected' and issuer is not null then
         -- The author rejected work; tell only its actual personal executor.
         if typ='personal' and target ~* '^[0-9a-f-]{36}$' then
           insert into public.promysel_push_events(field_id,user_id,event_key,task_id,title,body,category,route)
           select field,m.user_id,'task-rejected:'||task_id||':'||coalesce(t->>'rejectedAt',''),task_id,
             'Задание возвращено на доработку',left(coalesce(t->>'title','Задание'),180),'task','/tasks'
           from public.field_memberships m
           where m.field_id=field and m.user_id=target::uuid and m.approved and not m.blocked
             and m.user_id::text<>issuer
           on conflict(user_id,event_key) do nothing;
         end if;
       elsif current_state='confirmed' and typ='personal' and target ~* '^[0-9a-f-]{36}$' then
         insert into public.promysel_push_events(field_id,user_id,event_key,task_id,title,body,category,route)
         select field,m.user_id,'task-confirmed:'||task_id,task_id,
            'Задание принято',left(coalesce(t->>'title','Задание'),180),'task','/tasks'
         from public.field_memberships m
         where m.field_id=field and m.user_id=target::uuid and m.approved and not m.blocked
         on conflict(user_id,event_key) do nothing;
       end if;
     end if;
   end loop;
 end if;

 if jsonb_typeof(new.payload->'training')='array' then
   for item in select value from jsonb_array_elements(new.payload->'training') loop
     task_id:=item->>'id';user_ref:=item->>'userId';
     if task_id is null or length(task_id)>120 or
       user_ref is null or user_ref !~* '^[0-9a-f-]{36}$' then continue;end if;
     select value into old_item from jsonb_array_elements(
        case when jsonb_typeof(old_state->'training')='array' then old_state->'training' else '[]'::jsonb end)
        where value->>'id'=task_id limit 1;
     if item is distinct from old_item and item->>'completedAt' is null then
       insert into public.promysel_push_events(field_id,user_id,event_key,task_id,title,body,category,route)
       select field,m.user_id,'training-updated:'||task_id||':'||coalesce(item->>'updatedAt',item->>'date',''),
         task_id,'Назначено или изменено обучение',left(coalesce(item->>'title','Обучение'),180),'training','/menu'
       from public.field_memberships m
       where m.field_id=field and m.user_id=user_ref::uuid and m.approved and not m.blocked
       on conflict(user_id,event_key) do nothing;
     end if;
   end loop;
 end if;

 if jsonb_typeof(new.payload->'workSchedules')='object' then
   for user_ref,v in select key,value from jsonb_each(new.payload->'workSchedules') loop
     if user_ref !~* '^[0-9a-f-]{36}$' then continue;end if;
     if v is distinct from old_state->'workSchedules'->user_ref
       and new.actor_id::text<>user_ref then
       insert into public.promysel_push_events(field_id,user_id,event_key,task_id,title,body,category,route)
       select field,m.user_id,
         'schedule-changed:'||user_ref||':'||md5(v::text),user_ref,
         'Изменился ваш график','Проверьте вахту, отдых и отпуск','schedule','/menu'
       from public.field_memberships m where m.field_id=field and m.user_id=user_ref::uuid
          and m.approved and not m.blocked
       on conflict(user_id,event_key) do nothing;
     end if;
   end loop;
 end if;
 return new;
exception when others then
 raise warning 'promysel app notifications skipped SQLSTATE %',sqlstate;
 return new;
end $fn$;
drop trigger if exists zz_promysel_notification_v203 on public.sync_events;
create trigger zz_promysel_notification_v203 after insert on public.sync_events
for each row when (new.event_type='app_state')
execute function app_private.promysel_notify_app_state_v203();

create or replace function app_private.promysel_notify_registration_v203()
returns trigger language plpgsql security definer set search_path='' as $fn$
declare field text;
begin
 field:=coalesce(new.field_id,new.approved_field_id);
 if field is null then return new;end if;
 if tg_op='INSERT' and new.state='pending' or
   tg_op='UPDATE' and new.state='pending' and old.state is distinct from new.state then
   insert into public.promysel_push_events(field_id,user_id,event_key,task_id,title,body,category,route)
   select field,m.user_id,'registration-request:'||new.id,new.id::text,
      'Новая заявка сотрудника','Ожидает согласования','registration','/menu'
   from public.field_memberships m where m.field_id=field and m.role='shopChief'
     and m.approved and not m.blocked
   on conflict(user_id,event_key) do nothing;
 end if;
 return new;
exception when others then
 raise warning 'promysel registration notification skipped SQLSTATE %',sqlstate;
 return new;
end $fn$;
drop trigger if exists promysel_registration_notify_v203 on public.registration_requests;
create trigger promysel_registration_notify_v203
after insert or update of state on public.registration_requests
for each row execute function app_private.promysel_notify_registration_v203();

commit;
