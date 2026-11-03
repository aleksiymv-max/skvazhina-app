-- v1.79: administrative changes preserve well/pad and walk history.
-- Deleting fields archives them. Removing personnel deletes only their field membership.
alter table public.oil_fields add column if not exists archived_at timestamptz;
alter table public.field_memberships add column if not exists chief_id uuid references auth.users(id) on delete set null;
create index if not exists field_memberships_chief_idx on public.field_memberships(chief_id) where chief_id is not null;
alter table public.personnel_audit drop constraint if exists personnel_audit_action_check;
alter table public.personnel_audit add constraint personnel_audit_action_check check (
 action in ('approve','reject','role_change','block','unblock',
 'approve_request','approved_account_created','approval_started','approval_completed',
 'approval_failed','registration_rejected','admin_update','admin_remove',
 'field_archive','field_create','field_rename')
);
comment on column public.oil_fields.archived_at is 'Reversible administrative removal; production records and history remain untouched';

-- Push notifications about NEW assignments are queued only for on-shift recipients.
-- Calendars are stored in the app_state.workSchedules snapshot.
CREATE OR REPLACE FUNCTION app_private.promysel_employee_on_shift(p_state jsonb, p_user uuid, p_day date)
 RETURNS boolean
 LANGUAGE plpgsql
 STABLE
 SET search_path TO ''
AS $function$
declare v jsonb; period jsonb; anchor date; current_month int; first_of_month date; last_of_month date; boundary date; idx int;
begin
 v:=p_state->'workSchedules'->(p_user::text);
 if v is null then return false; end if;
 if jsonb_typeof(v->'leave')='array' then
  for period in select value from jsonb_array_elements(v->'leave')
  loop
   if p_day between (period->>'start')::date and (period->>'end')::date then return false; end if;
  end loop;
 end if;
 if jsonb_typeof(v->'overrides')='array' then
  for idx in reverse (select count(*)::int from jsonb_array_elements(v->'overrides'))-1..0 loop
   period:=v->'overrides'->idx;
   if p_day between (period->>'start')::date and (period->>'end')::date then return period->>'type'='work'; end if;
  end loop;
 end if;
 anchor:=nullif(v->>'arrival','')::date;
 if anchor is null or p_day<anchor then return false; end if;
 current_month:=(extract(year from p_day)::int-extract(year from anchor)::int)*12+(extract(month from p_day)::int-extract(month from anchor)::int);
 first_of_month:=(date_trunc('month',anchor)::date+make_interval(months=>current_month))::date;
 last_of_month:=(first_of_month+interval '1 month - 1 day')::date;
 boundary:=first_of_month+(least(extract(day from anchor)::int,extract(day from last_of_month)::int)-1);
 if p_day<boundary then current_month:=current_month-1; end if;
 return mod(current_month,2)=0;
exception when others then return false;
end $function$;

CREATE OR REPLACE FUNCTION app_private.promysel_queue_task_push()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
DECLARE
  previous jsonb := '[]'::jsonb;
  task jsonb;
  past jsonb;
  identifier text;
  issuer text;
  recipient text;
  task_title text;
  completion text;
  dedup text;
BEGIN
  IF NEW.event_type <> 'app_state' OR jsonb_typeof(NEW.payload->'tasks') <> 'array' THEN
    RETURN NEW;
  END IF;
  SELECT COALESCE(e.payload->'tasks', '[]'::jsonb)
    INTO previous
    FROM public.sync_events e
   WHERE e.field_id = NEW.field_id AND e.event_type = 'app_state' AND e.sequence < NEW.sequence
   ORDER BY e.sequence DESC LIMIT 1;
  previous := COALESCE(previous, '[]'::jsonb);
  FOR task IN SELECT value FROM jsonb_array_elements(NEW.payload->'tasks') LOOP
    identifier := task->>'id';
    IF identifier IS NULL OR length(identifier) > 120 THEN CONTINUE; END IF;
    SELECT value INTO past FROM jsonb_array_elements(previous) WHERE value->>'id' = identifier LIMIT 1;
    issuer := task->>'createdById';
    recipient := task->>'targetId';
    task_title := left(COALESCE(task->>'title', 'Задание'), 180);
    IF past IS NULL AND task->>'status' = 'active' AND
      COALESCE((task->>'createdAt')::timestamptz, now()) >= now() - interval '2 days' THEN
      dedup := 'task-created:' || identifier;
      IF task->>'targetType' = 'personal' AND recipient ~* '^[0-9a-f-]{36}$' THEN
        INSERT INTO public.promysel_push_events(field_id, user_id, event_key, task_id, title, body)
        SELECT NEW.field_id,m.user_id,dedup,identifier,'Новое задание',task_title
        FROM public.field_memberships m
        WHERE m.field_id=NEW.field_id AND m.user_id=recipient::uuid
          AND m.approved AND NOT m.blocked
          AND app_private.promysel_employee_on_shift(NEW.payload,m.user_id,now()::date)
        ON CONFLICT (user_id, event_key) DO NOTHING;
      ELSIF task->>'targetType' IN ('area','pad') THEN
        INSERT INTO public.promysel_push_events(field_id,user_id,event_key,task_id,title,body)
        SELECT NEW.field_id,m.user_id,dedup,identifier,'Новое общее задание',task_title
          FROM public.field_memberships m
         WHERE m.field_id=NEW.field_id AND m.approved AND NOT m.blocked
           AND (issuer IS NULL OR m.user_id::text<>issuer)
           AND app_private.promysel_employee_on_shift(NEW.payload,m.user_id,now()::date)
        ON CONFLICT (user_id, event_key) DO NOTHING;
      END IF;
    ELSIF past IS NOT NULL AND COALESCE(past->>'status','')='active' AND
          task->>'status'='awaitingConfirmation' THEN
      completion := task->>'completedAt';
      dedup := 'task-completed:' || identifier || ':' || COALESCE(completion,'');
      INSERT INTO public.promysel_push_events(field_id,user_id,event_key,task_id,title,body)
      SELECT NEW.field_id,m.user_id,dedup,identifier,'Задание выполнено',
        left(task_title || ' · ' || COALESCE(task->>'completedBy', 'Исполнитель'), 240)
        FROM public.field_memberships m
       WHERE m.field_id=NEW.field_id AND m.approved AND NOT m.blocked
         AND (m.user_id::text=issuer AND (task->>'targetType' <> 'personal' OR m.user_id::text IS DISTINCT FROM recipient))
      ON CONFLICT (user_id, event_key) DO NOTHING;
    END IF;
  END LOOP;
  RETURN NEW;
EXCEPTION WHEN OTHERS THEN
  RAISE WARNING 'Promysel push queue skipped: SQLSTATE %', SQLSTATE;
  RETURN NEW;
END;
$function$;
