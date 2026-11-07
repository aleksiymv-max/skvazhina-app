-- Additive per-field dispatcher submission ledger. No existing table modified.
CREATE TABLE IF NOT EXISTS public.promysel_problem_dispatches (
 field_id text NOT NULL REFERENCES public.oil_fields(id),
 problem_key text NOT NULL CHECK (
   problem_key ~ '^(measurement|report):[0-9a-fA-F-]{36}$'
 ),
 filed_at timestamptz NOT NULL DEFAULT now(),
 filed_by uuid NOT NULL DEFAULT auth.uid(),
 filed_by_name text NOT NULL DEFAULT '',
 PRIMARY KEY (field_id,problem_key)
);
ALTER TABLE public.promysel_problem_dispatches ENABLE ROW LEVEL SECURITY;
-- Read the status only inside one's approved, non-blocked field.
CREATE POLICY promysel_dispatch_read ON public.promysel_problem_dispatches
 FOR SELECT TO authenticated USING (app_private.is_member(field_id));
-- Only an explicitly assigned dispatcher may record the submission.
CREATE POLICY promysel_dispatch_insert ON public.promysel_problem_dispatches
 FOR INSERT TO authenticated WITH CHECK (
   filed_by = (select auth.uid())
   AND EXISTS (
     SELECT 1 FROM public.field_memberships m
     WHERE m.field_id=promysel_problem_dispatches.field_id
       AND m.user_id=(select auth.uid())
       AND m.approved AND NOT m.blocked
       AND (m.role='dispatcher' OR m.subrole='dispatcher')
   )
 );
-- The server, not the client, sets the audit timestamp and author's name.
CREATE FUNCTION app_private.promysel_stamp_dispatch()
RETURNS trigger LANGUAGE plpgsql SECURITY INVOKER SET search_path='' AS $$
DECLARE actor text;
BEGIN
 IF auth.uid() IS NULL OR NEW.filed_by IS DISTINCT FROM auth.uid() THEN
    RAISE EXCEPTION 'Authenticated dispatcher required' USING ERRCODE='42501';
 END IF;
 SELECT m.display_name INTO actor FROM public.field_memberships m
 WHERE m.user_id=auth.uid() AND m.field_id=NEW.field_id
 AND m.approved AND NOT m.blocked
 AND (m.role='dispatcher' OR m.subrole='dispatcher')
 LIMIT 1;
 IF actor IS NULL THEN
   RAISE EXCEPTION 'Dispatcher role required' USING ERRCODE='42501';
 END IF;
 NEW.filed_at:=now();NEW.filed_by:=auth.uid();NEW.filed_by_name:=actor;
 RETURN NEW;
END;
$$;
CREATE TRIGGER promysel_stamp_dispatch
 BEFORE INSERT ON public.promysel_problem_dispatches
 FOR EACH ROW EXECUTE FUNCTION app_private.promysel_stamp_dispatch();
REVOKE ALL ON TABLE public.promysel_problem_dispatches FROM PUBLIC, anon, authenticated;
GRANT SELECT, INSERT ON TABLE public.promysel_problem_dispatches TO authenticated;
REVOKE ALL ON FUNCTION app_private.promysel_stamp_dispatch() FROM PUBLIC, anon, authenticated;
