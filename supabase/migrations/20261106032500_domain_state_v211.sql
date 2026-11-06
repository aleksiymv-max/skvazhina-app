-- v2.11: domain-isolated, optimistic-versioned snapshots for field operations.
-- Legacy sync_events and existing history are retained without migration/rewrite.
CREATE TABLE IF NOT EXISTS public.promysel_sync_domain_state (
 field_id text NOT NULL REFERENCES public.oil_fields(id) ON DELETE RESTRICT,
 domain text NOT NULL CHECK (domain IN ('tasks','schedules','training','structure')),
 payload jsonb NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(payload)='object' AND pg_column_size(payload)<=4194304),
 revision bigint NOT NULL DEFAULT 0 CHECK(revision>=0),
 last_mutation_key text NOT NULL DEFAULT '',
 updated_by uuid REFERENCES auth.users(id) ON DELETE SET NULL,
 updated_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY(field_id,domain)
);
ALTER TABLE public.promysel_sync_domain_state ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.promysel_sync_domain_state FROM PUBLIC,anon,authenticated;
GRANT SELECT,INSERT,UPDATE ON public.promysel_sync_domain_state TO service_role;

-- Signals contain NO employee names, tasks, schedules, or measurements.
ALTER TABLE public.sync_events DROP CONSTRAINT IF EXISTS sync_events_event_type_check;
ALTER TABLE public.sync_events ADD CONSTRAINT sync_events_event_type_check CHECK (
 event_type=ANY(ARRAY[
  'measurement','app_state','task','problem','annulus_pressure',
  'training','notification','equipment','repair','avatar_change','domain_change'
 ]::text[]));
CREATE INDEX IF NOT EXISTS sync_events_field_domain_signal_idx
  ON public.sync_events(field_id,sequence) WHERE event_type='domain_change';

CREATE OR REPLACE FUNCTION public.promysel_commit_sync_domain(
 p_field_id text,p_domain text,p_mutation_key text,p_device_id text,
 p_actor uuid,p_expected_revision bigint,p_payload jsonb
) RETURNS jsonb
LANGUAGE plpgsql SECURITY INVOKER SET search_path TO ''
AS $function$
DECLARE
 v_old public.promysel_sync_domain_state%rowtype;
 v_revision bigint:=0;
 v_merged jsonb;
 v_old_schedules jsonb;
 v_new_schedules jsonb;
 v_schedule_key text;
 v_schedule_val jsonb;
 v_prior_val jsonb;
 v_deleted jsonb;
 v_kind text;
 v_arr jsonb;
 v_marker jsonb;
 v_is_admin boolean;
BEGIN
 IF p_domain NOT IN ('tasks','schedules','training','structure')
   OR length(p_mutation_key) NOT BETWEEN 8 AND 300
   OR length(p_device_id) NOT BETWEEN 1 AND 200
   OR jsonb_typeof(p_payload)<>'object'
   OR p_expected_revision IS NULL OR p_expected_revision<0
   OR coalesce(p_payload->>'fieldId','')<>p_field_id
 THEN RAISE EXCEPTION 'Invalid domain mutation' USING ERRCODE='22023'; END IF;
 IF NOT EXISTS(SELECT 1 FROM public.oil_fields f
   WHERE f.id=p_field_id AND f.archived_at IS NULL)
 THEN RAISE EXCEPTION 'Field unavailable' USING ERRCODE='42501'; END IF;
 SELECT coalesce(u.raw_app_meta_data->>'system_admin'='true',false)
   INTO v_is_admin FROM auth.users u WHERE u.id=p_actor;
 IF NOT coalesce(v_is_admin,false) AND NOT EXISTS(
  SELECT 1 FROM public.field_memberships m
  WHERE m.field_id=p_field_id AND m.user_id=p_actor
    AND m.approved AND NOT m.blocked)
 THEN RAISE EXCEPTION 'Field membership revoked' USING ERRCODE='42501';END IF;
 -- Lock all writes to the same domain; unrelated domains remain independent.
 PERFORM pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended(p_field_id||'/'||p_domain,46111));
 SELECT * INTO v_old FROM public.promysel_sync_domain_state
  WHERE field_id=p_field_id AND domain=p_domain FOR UPDATE;
 IF FOUND THEN
   IF v_old.last_mutation_key=p_mutation_key THEN
     RETURN jsonb_build_object('status','duplicate','revision',v_old.revision);
   END IF;
   v_revision:=v_old.revision;
 END IF;
 IF v_revision<>p_expected_revision THEN
   RETURN jsonb_build_object('status','conflict','revision',v_revision);
 END IF;
 v_merged:=app_private.promysel_merge_state_snapshots(
   CASE WHEN v_revision=0 THEN '{}'::jsonb ELSE v_old.payload END,p_payload);
 -- Preserve each employee's schedule independently, using version timestamps.
 IF p_domain='schedules' THEN
   v_old_schedules:=CASE WHEN jsonb_typeof(v_old.payload->'workSchedules')='object'
     THEN v_old.payload->'workSchedules' ELSE '{}'::jsonb END;
   v_new_schedules:=CASE WHEN jsonb_typeof(p_payload->'workSchedules')='object'
     THEN p_payload->'workSchedules' ELSE '{}'::jsonb END;
   FOR v_schedule_key,v_schedule_val IN
     SELECT key,value FROM jsonb_each(v_new_schedules)
   LOOP
     v_prior_val:=v_old_schedules->v_schedule_key;
     IF v_prior_val IS NULL OR
       coalesce((v_schedule_val->>'updated')::timestamptz,'epoch'::timestamptz)>=
       coalesce((v_prior_val->>'updated')::timestamptz,'epoch'::timestamptz)
     THEN
       v_old_schedules:=jsonb_set(v_old_schedules,ARRAY[v_schedule_key],v_schedule_val,true);
     END IF;
   END LOOP;
   v_merged:=jsonb_set(v_merged,'{workSchedules}',v_old_schedules,true);
 END IF;
 -- Training and structure deletion markers only grow; stale devices cannot
 -- revive a deleted record by omitting a marker from their own copy.
 IF p_domain='training' THEN
   SELECT coalesce(jsonb_agg(DISTINCT value),'[]'::jsonb) INTO v_deleted
     FROM jsonb_array_elements_text(
       coalesce(v_old.payload->'trainingDeletedIds','[]'::jsonb) ||
       coalesce(p_payload->'trainingDeletedIds','[]'::jsonb));
   v_merged:=jsonb_set(v_merged,'{trainingDeletedIds}',v_deleted,true);
   v_merged:=jsonb_set(v_merged,'{training}',(
     SELECT coalesce(jsonb_agg(item),'[]'::jsonb) FROM jsonb_array_elements(
       coalesce(v_merged->'training','[]'::jsonb)) item
     WHERE NOT(v_deleted ? (item->>'id'))
   ),true);
 END IF;
 IF p_domain='structure' THEN
   v_marker:='{}'::jsonb;
   FOREACH v_kind IN ARRAY ARRAY['areas','pads','wells'] LOOP
      SELECT coalesce(jsonb_agg(DISTINCT value),'[]'::jsonb) INTO v_arr
       FROM jsonb_array_elements_text(
         coalesce(v_old.payload->'structureDeleted'->v_kind,'[]'::jsonb) ||
         coalesce(p_payload->'structureDeleted'->v_kind,'[]'::jsonb));
      v_marker:=jsonb_set(v_marker,ARRAY[v_kind],v_arr,true);
   END LOOP;
   v_merged:=jsonb_set(v_merged,'{structureDeleted}',v_marker,true);
 END IF;
 INSERT INTO public.promysel_sync_domain_state
    (field_id,domain,payload,revision,last_mutation_key,updated_by)
 VALUES(p_field_id,p_domain,v_merged,v_revision+1,p_mutation_key,p_actor)
 ON CONFLICT (field_id,domain) DO UPDATE
 SET payload=excluded.payload,revision=excluded.revision,
     last_mutation_key=excluded.last_mutation_key,
     updated_by=excluded.updated_by,updated_at=now();
 INSERT INTO public.sync_events
  (event_key,field_id,device_id,event_type,payload,actor_id,client_updated_at)
 VALUES(p_mutation_key,p_field_id,p_device_id,'domain_change',
   jsonb_build_object('domain',p_domain,'revision',v_revision+1),p_actor,now())
 ON CONFLICT(event_key) DO NOTHING;
 RETURN jsonb_build_object('status','accepted','revision',v_revision+1);
END $function$;
REVOKE ALL ON FUNCTION public.promysel_commit_sync_domain(
 text,text,text,text,uuid,bigint,jsonb) FROM PUBLIC,anon,authenticated;
GRANT EXECUTE ON FUNCTION public.promysel_commit_sync_domain(
 text,text,text,text,uuid,bigint,jsonb) TO service_role;
