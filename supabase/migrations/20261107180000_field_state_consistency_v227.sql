-- v2.27: Authoritative, field-scoped well statuses and measurement problem closures.
-- Additive only. Existing measurements, old statuses, sync events and user data stay intact.
CREATE TABLE IF NOT EXISTS public.promysel_field_well_states (
 field_id text NOT NULL REFERENCES public.oil_fields(id),
 well_id text NOT NULL CHECK (length(well_id) BETWEEN 1 AND 160),
 status text NOT NULL CHECK (status IN ('working','stopped','workover')),
 client_updated_at timestamptz NOT NULL,
 server_received_at timestamptz NOT NULL DEFAULT now(),
 updated_by uuid NOT NULL DEFAULT auth.uid(),
 PRIMARY KEY(field_id,well_id)
);
ALTER TABLE public.promysel_field_well_states ENABLE ROW LEVEL SECURITY;
CREATE POLICY promysel_field_well_state_read ON public.promysel_field_well_states
 FOR SELECT TO authenticated USING(app_private.is_member(field_id));
CREATE POLICY promysel_field_well_state_insert ON public.promysel_field_well_states
 FOR INSERT TO authenticated WITH CHECK(
 updated_by=(select auth.uid()) AND app_private.is_member(field_id)
 AND EXISTS(SELECT 1 FROM public.field_memberships m
  WHERE m.field_id=field_id AND m.user_id=auth.uid()
  AND m.approved AND NOT m.blocked AND m.role IN ('operator','engineer','shopChief'))
 );
CREATE POLICY promysel_field_well_state_update ON public.promysel_field_well_states
 FOR UPDATE TO authenticated USING(
 app_private.is_member(field_id)
 AND EXISTS(SELECT 1 FROM public.field_memberships m
  WHERE m.field_id=field_id AND m.user_id=auth.uid()
  AND m.approved AND NOT m.blocked AND m.role IN ('operator','engineer','shopChief'))
 ) WITH CHECK(
 app_private.is_member(field_id)
 AND EXISTS(SELECT 1 FROM public.field_memberships m
  WHERE m.field_id=field_id AND m.user_id=auth.uid()
  AND m.approved AND NOT m.blocked AND m.role IN ('operator','engineer','shopChief'))
 );
-- Incoming offline writes keep their original edit time. A delayed stale write
-- cannot overwrite a newer value published by another device.
CREATE FUNCTION app_private.promysel_stamp_well_state()
RETURNS trigger LANGUAGE plpgsql SECURITY INVOKER SET search_path='' AS $$
BEGIN
 IF auth.uid() IS NULL THEN RAISE EXCEPTION 'Authentication required' USING ERRCODE='42501'; END IF;
 IF NEW.client_updated_at>now()+interval '5 minutes' THEN NEW.client_updated_at:=now(); END IF;
 IF TG_OP='UPDATE' AND NEW.client_updated_at<=OLD.client_updated_at THEN RETURN OLD; END IF;
 NEW.updated_by:=auth.uid();
 NEW.server_received_at:=now();
 RETURN NEW;
END;
$$;
CREATE TRIGGER promysel_stamp_well_state BEFORE INSERT OR UPDATE
 ON public.promysel_field_well_states FOR EACH ROW
 EXECUTE FUNCTION app_private.promysel_stamp_well_state();
REVOKE ALL ON TABLE public.promysel_field_well_states FROM PUBLIC,anon,authenticated;
GRANT SELECT,INSERT ON public.promysel_field_well_states TO authenticated;
GRANT UPDATE(status,client_updated_at,updated_by) ON public.promysel_field_well_states TO authenticated;
REVOKE ALL ON FUNCTION app_private.promysel_stamp_well_state() FROM PUBLIC,anon,authenticated;

CREATE TABLE IF NOT EXISTS public.promysel_measurement_problem_resolutions (
 field_id text NOT NULL REFERENCES public.oil_fields(id),
 measurement_key text NOT NULL CHECK(measurement_key LIKE 'measurement:%' AND length(measurement_key)<=240),
 resolved_at timestamptz NOT NULL DEFAULT now(),
 resolved_by uuid NOT NULL DEFAULT auth.uid(),
 resolved_by_name text NOT NULL DEFAULT '',
 PRIMARY KEY(field_id,measurement_key)
);
ALTER TABLE public.promysel_measurement_problem_resolutions ENABLE ROW LEVEL SECURITY;
CREATE POLICY promysel_measurement_resolution_read ON public.promysel_measurement_problem_resolutions
 FOR SELECT TO authenticated USING(app_private.is_member(field_id));
CREATE POLICY promysel_measurement_resolution_insert ON public.promysel_measurement_problem_resolutions
 FOR INSERT TO authenticated WITH CHECK(
 resolved_by=(select auth.uid()) AND app_private.can_resolve_problem(field_id));
-- Immutable closures; no UPDATE or DELETE permissions or policies.
CREATE FUNCTION app_private.promysel_stamp_problem_resolution()
RETURNS trigger LANGUAGE plpgsql SECURITY INVOKER SET search_path='' AS $$
DECLARE real_name text;
BEGIN
 IF auth.uid() IS NULL OR NEW.resolved_by IS DISTINCT FROM auth.uid() THEN
   RAISE EXCEPTION 'Resolver mismatch' USING ERRCODE='42501';
 END IF;
 IF NOT app_private.can_resolve_problem(NEW.field_id) THEN
   RAISE EXCEPTION 'No permission to resolve problem' USING ERRCODE='42501';
 END IF;
 SELECT m.display_name INTO real_name FROM public.field_memberships m
  WHERE m.field_id=NEW.field_id AND m.user_id=auth.uid() AND m.approved AND NOT m.blocked
  LIMIT 1;
 IF real_name IS NULL THEN RAISE EXCEPTION 'Inactive membership' USING ERRCODE='42501'; END IF;
 NEW.resolved_at:=now(); NEW.resolved_by_name:=real_name;
 RETURN NEW;
END;
$$;
CREATE TRIGGER promysel_stamp_problem_resolution BEFORE INSERT
 ON public.promysel_measurement_problem_resolutions FOR EACH ROW
 EXECUTE FUNCTION app_private.promysel_stamp_problem_resolution();
REVOKE ALL ON TABLE public.promysel_measurement_problem_resolutions FROM PUBLIC,anon,authenticated;
GRANT SELECT,INSERT ON TABLE public.promysel_measurement_problem_resolutions TO authenticated;
REVOKE ALL ON FUNCTION app_private.promysel_stamp_problem_resolution() FROM PUBLIC,anon,authenticated;
