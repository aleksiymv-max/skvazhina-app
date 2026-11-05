-- v2.03b: time-based reminders and tightly scoped problem/administrator events.
-- One daily reminder scan; trigger-based changes remain immediate.
begin;
create or replace function app_private.promysel_notify_problems_v203()
returns trigger language plpgsql security definer set search_path='' as $fn$
declare previous jsonb:='{}'::jsonb; issue text; detail jsonb;
begin
 if new.event_type<>'app_state'
   or jsonb_typeof(new.payload->'problemApplications')<>'object'
   or new.payload->'problemApplications'='{}'::jsonb then return new; end if;
 select coalesce(e.payload->'problemApplications','{}'::jsonb) into previous
 from public.sync_events e where e.field_id=new.field_id and e.event_type='app_state'
   and e.sequence<new.sequence order by e.sequence desc limit 1;
 previous:=coalesce(previous,'{}'::jsonb);
 for issue,detail in select key,value from jsonb_each(new.payload->'problemApplications') loop
   if detail is distinct from previous->issue then
     insert into public.promysel_push_events(field_id,user_id,event_key,task_id,
       title,body,category,route)
     select new.field_id,m.user_id,'problem-change:'||new.sequence||':'||md5(issue),left(issue,160),
       'Обновлена проблема по скважине','Проверьте состояние производственной проблемы',
       'problem','/wells'
     from public.field_memberships m where m.field_id=new.field_id and m.approved
       and not m.blocked and m.role in('engineer','shopChief') and
       m.user_id<>new.actor_id
     on conflict(user_id,event_key) do nothing;
   end if;
 end loop;
 return new;
exception when others then
 raise warning 'promysel problem notification skipped SQLSTATE %',sqlstate;
 return new;
end $fn$;
drop trigger if exists zz_promysel_problem_notifications_v203 on public.sync_events;
create trigger zz_promysel_problem_notifications_v203
after insert on public.sync_events for each row when(new.event_type='app_state')
execute function app_private.promysel_notify_problems_v203();

create or replace function app_private.promysel_admin_requests_v203()
returns trigger language plpgsql security definer set search_path='' as $fn$
begin
 if new.state='pending' and new.requested_role='shopChief'
   and new.field_id is null and new.proposed_field_name is not null then
   insert into public.promysel_push_events(field_id,user_id,event_key,task_id,
     title,body,category,route)
   select 'field-admin',u.id,'new-chief-request:'||new.id::text,new.id::text,
     'Новая заявка начальника цеха','Необходимо согласовать создание месторождения',
     'registration','/menu'
   from auth.users u where u.raw_app_meta_data->>'system_admin'='true'
   on conflict(user_id,event_key) do nothing;
 end if;
 return new;
exception when others then
 raise warning 'promysel admin request notice SQLSTATE %',sqlstate;
 return new;
end $fn$;
drop trigger if exists zz_promysel_admin_requests_v203 on public.registration_requests;
create trigger zz_promysel_admin_requests_v203
after insert or update of state on public.registration_requests
for each row execute function app_private.promysel_admin_requests_v203();

create or replace function app_private.promysel_daily_reminders_v203()
returns integer language plpgsql security definer set search_path='' as $fn$
declare today date:=(now() at time zone 'Asia/Tomsk')::date;
  snap record; item jsonb; kv record; d date; days_left integer;
  total integer:=0; status text; before_status boolean; start_status boolean;
  uid uuid; task_id text;
begin
 for snap in
   select distinct on(field_id) field_id,payload
   from public.sync_events
   where event_type='app_state'
   order by field_id,sequence desc
 loop
   if jsonb_typeof(snap.payload->'training')='array' then
     for item in select value from jsonb_array_elements(snap.payload->'training') loop
       if item->>'completedAt' is not null or item->>'userId' is null
          or item->>'userId' !~* '^[0-9a-f-]{36}$'
          or item->>'date' is null then continue;end if;
       begin
         d:=left(item->>'date',10)::date;days_left:=d-today;
       exception when others then continue;end;
       if days_left not in (7,3,1,0,-1) then continue;end if;
       task_id:=coalesce(item->>'id','');
       if task_id='' or length(task_id)>120 then continue;end if;
       insert into public.promysel_push_events(field_id,user_id,event_key,task_id,
           title,body,category,route)
       select snap.field_id,m.user_id,
         'training-reminder:'||task_id||':'||today::text,
         task_id,
         case when days_left<0 then 'Просрочено обучение' else 'Скоро обучение' end,
         left(coalesce(item->>'title','Обучение'),180),
         'training','/menu'
       from public.field_memberships m
       where m.field_id=snap.field_id and m.user_id=(item->>'userId')::uuid
         and m.approved and not m.blocked
       on conflict(user_id,event_key) do nothing;
       get diagnostics total=total+row_count;
     end loop;
   end if;

   if jsonb_typeof(snap.payload->'workSchedules')='object' then
     for kv in select key,value from jsonb_each(snap.payload->'workSchedules') loop
       if kv.key !~* '^[0-9a-f-]{36}$' then continue;end if;
       uid:=kv.key::uuid;
       for days_left in select unnest(array[7,3,1,0]) loop
         d:=today+days_left;
         start_status:=app_private.promysel_employee_on_shift(snap.payload,uid,d);
         before_status:=app_private.promysel_employee_on_shift(snap.payload,uid,d-1);
         if not start_status or before_status then continue;end if;
         insert into public.promysel_push_events(field_id,user_id,event_key,task_id,
           title,body,category,route)
         select snap.field_id,m.user_id,
           'shift-start:'||kv.key||':'||d::text||':'||days_left::text,
           kv.key,
           case when days_left=0 then 'Сегодня начало вахты' else 'Скоро вахта' end,
           case when days_left=0 then 'Проверьте график и время выхода'
             else 'До начала вахты: '||days_left::text||' дн.' end,
           'schedule','/menu'
         from public.field_memberships m
         where m.field_id=snap.field_id and m.user_id=uid and m.approved and not m.blocked
         on conflict(user_id,event_key) do nothing;
         get diagnostics total=total+row_count;
       end loop;
       -- Vacation starts are time-based, including when employee isn't on shift.
       if jsonb_typeof(kv.value->'leave')='array' then
         for item in select value from jsonb_array_elements(kv.value->'leave') loop
           begin
             d:=left(item->>'start',10)::date;days_left:=d-today;
           exception when others then continue;end;
           if days_left not in (7,3,1,0) then continue;end if;
           insert into public.promysel_push_events(field_id,user_id,event_key,task_id,
             title,body,category,route)
           select snap.field_id,m.user_id,
             'leave-start:'||kv.key||':'||d::text||':'||days_left::text,
             kv.key,'Скоро отпуск','Проверьте график отпуска',
             'schedule','/menu'
           from public.field_memberships m
           where m.field_id=snap.field_id and m.user_id=uid and m.approved and not m.blocked
           on conflict(user_id,event_key) do nothing;
           get diagnostics total=total+row_count;
         end loop;
       end if;
     end loop;
   end if;

   -- Task deadlines, when present in the new or old task schema.
   if jsonb_typeof(snap.payload->'tasks')='array' then
     for item in select value from jsonb_array_elements(snap.payload->'tasks') loop
       if item->>'status'<>'active' or item->>'targetType'<>'personal'
         or item->>'targetId' !~* '^[0-9a-f-]{36}$' then continue;end if;
       begin
         d:=left(coalesce(item->>'dueDate',item->>'deadline'),10)::date;
         days_left:=d-today;
       exception when others then continue;end;
       if days_left not in (3,1,0,-1) then continue;end if;
       task_id:=item->>'id';
       if task_id is null or length(task_id)>120 then continue;end if;
       insert into public.promysel_push_events(field_id,user_id,event_key,task_id,
         title,body,category,route)
       select snap.field_id,m.user_id,'task-deadline:'||task_id||':'||today::text,
         task_id,case when days_left<0 then 'Задание просрочено' else 'Срок задания близко' end,
         left(coalesce(item->>'title','Задание'),180),'task','/tasks'
       from public.field_memberships m where m.field_id=snap.field_id
         and m.user_id=(item->>'targetId')::uuid and m.approved and not m.blocked
       on conflict(user_id,event_key) do nothing;
       get diagnostics total=total+row_count;
     end loop;
   end if;
 end loop;
 return total;
end $fn$;
revoke all on function app_private.promysel_daily_reminders_v203() from public,anon,authenticated;
commit;
