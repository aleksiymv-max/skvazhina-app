-- v2.11: Domain task writes must feed existing task push outbox,
-- without publishing private tasks in sync_events domain_change signals.
CREATE OR REPLACE FUNCTION app_private.promysel_notify_task_domain_v211()
RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path TO ''
AS $function$
DECLARE
 old_rows jsonb:='[]'::jsonb;
 legacy_state jsonb:='{}'::jsonb;
 schedule_state jsonb:='{}'::jsonb;
 notification_state jsonb:='{}'::jsonb;
 t jsonb;
 prior jsonb;
 ident text;
 issuer text;
 recipient text;
 title_text text;
 dedup text;
 actor_text text;
BEGIN
 IF new.domain<>'tasks' THEN RETURN new; END IF;
 SELECT e.payload INTO legacy_state FROM public.sync_events e
   WHERE e.field_id=new.field_id AND e.event_type='app_state'
   ORDER BY e.sequence DESC LIMIT 1;
 legacy_state:=coalesce(legacy_state,'{}'::jsonb);
 IF tg_op='UPDATE' THEN old_rows:=coalesce(old.payload->'tasks','[]'::jsonb); END IF;
 SELECT d.payload INTO schedule_state FROM public.promysel_sync_domain_state d
   WHERE d.field_id=new.field_id AND d.domain='schedules';
 notification_state:=pg_catalog.jsonb_set(legacy_state,'{workSchedules}',
   coalesce(legacy_state->'workSchedules','{}'::jsonb) ||
   coalesce(schedule_state->'workSchedules','{}'::jsonb),true);
 FOR t IN SELECT value FROM jsonb_array_elements(coalesce(new.payload->'tasks','[]'::jsonb)) LOOP
   ident:=t->>'id';issuer:=t->>'createdById';recipient:=t->>'targetId';
   title_text:=left(coalesce(t->>'title','Задание'),180);
   IF ident IS NULL OR length(ident)>120 THEN CONTINUE; END IF;
   SELECT value INTO prior FROM jsonb_array_elements(old_rows)
     WHERE value->>'id'=ident LIMIT 1;
   IF prior IS NULL THEN
     SELECT value INTO prior FROM jsonb_array_elements(
       coalesce(legacy_state->'tasks','[]'::jsonb))
       WHERE value->>'id'=ident LIMIT 1;
   END IF;
   IF prior IS NULL AND t->>'status'='active' AND
     coalesce(nullif(t->>'createdAt','')::timestamptz,now())>=now()-interval '2 days' THEN
      dedup:='task-created:'||ident;
      IF t->>'targetType'='personal' AND recipient ~* '^[0-9a-f-]{36}$' THEN
       INSERT INTO public.promysel_push_events(field_id,user_id,event_key,task_id,title,body)
        SELECT new.field_id,m.user_id,dedup,ident,'Новое задание',title_text
        FROM public.field_memberships m
        WHERE m.field_id=new.field_id AND m.user_id::text=recipient
          AND m.approved AND NOT m.blocked
          AND app_private.promysel_employee_on_shift(notification_state,m.user_id,now()::date)
        ON CONFLICT(user_id,event_key) DO NOTHING;
      ELSIF t->>'targetType' IN ('area','pad') THEN
       INSERT INTO public.promysel_push_events(field_id,user_id,event_key,task_id,title,body)
        SELECT new.field_id,m.user_id,dedup,ident,'Новое общее задание',title_text
        FROM public.field_memberships m
        WHERE m.field_id=new.field_id AND m.approved AND NOT m.blocked
          AND (issuer IS NULL OR m.user_id::text<>issuer)
          AND app_private.promysel_employee_on_shift(notification_state,m.user_id,now()::date)
        ON CONFLICT(user_id,event_key) DO NOTHING;
      END IF;
   ELSIF prior IS NOT NULL AND coalesce(prior->>'status','active')='active'
         AND t->>'status'='awaitingConfirmation' THEN
     dedup:='task-completed:'||ident||':'||coalesce(t->>'completedAt','');
     INSERT INTO public.promysel_push_events(field_id,user_id,event_key,task_id,title,body)
       SELECT new.field_id,m.user_id,dedup,ident,'Задание выполнено',
       left(title_text||' · '||coalesce(t->>'completedBy','Исполнитель'),240)
       FROM public.field_memberships m
       WHERE m.field_id=new.field_id AND m.approved AND NOT m.blocked
         AND m.user_id::text=issuer
         AND (t->>'targetType'<>'personal' OR m.user_id::text IS DISTINCT FROM recipient)
       ON CONFLICT(user_id,event_key) DO NOTHING;
   END IF;
 END LOOP;
 RETURN new;
EXCEPTION WHEN OTHERS THEN
 RAISE WARNING 'Domain task push queue skipped SQLSTATE %',SQLSTATE;
 RETURN new;
END $function$;
DROP TRIGGER IF EXISTS zz_promysel_domain_task_notification_v211
  ON public.promysel_sync_domain_state;
CREATE TRIGGER zz_promysel_domain_task_notification_v211
AFTER INSERT OR UPDATE OF payload ON public.promysel_sync_domain_state
FOR EACH ROW WHEN (new.domain='tasks')
EXECUTE FUNCTION app_private.promysel_notify_task_domain_v211();
REVOKE ALL ON FUNCTION app_private.promysel_notify_task_domain_v211()
FROM PUBLIC,anon,authenticated;
