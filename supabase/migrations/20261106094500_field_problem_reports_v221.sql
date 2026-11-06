-- v2.21. Standalone problems: no fake well measurements, no loss of offline work.
-- Limited to authenticated, approved members of the selected field.
CREATE TABLE IF NOT EXISTS public.field_problem_reports (
  id uuid PRIMARY KEY,
  field_id text NOT NULL REFERENCES public.oil_fields(id),
  area_id text NOT NULL CHECK (length(trim(area_id)) BETWEEN 1 AND 120),
  area_name text NOT NULL CHECK (length(trim(area_name)) BETWEEN 1 AND 180),
  pad_id text NOT NULL CHECK (length(trim(pad_id)) BETWEEN 1 AND 120),
  pad_name text NOT NULL CHECK (length(trim(pad_name)) BETWEEN 1 AND 180),
  well_id text,
  well_number text,
  description text NOT NULL CHECK (length(trim(description)) BETWEEN 3 AND 2000),
  author_id uuid NOT NULL DEFAULT auth.uid(),
  author_name text NOT NULL DEFAULT '',
  client_created_at timestamptz NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  status text NOT NULL DEFAULT 'open' CHECK (status IN ('open','resolved')),
  resolved_at timestamptz,
  resolved_by uuid,
  CONSTRAINT field_report_optional_well_pair CHECK (
    (well_id IS NULL AND well_number IS NULL) OR
    (well_id IS NOT NULL AND well_number IS NOT NULL)
  )
);
CREATE INDEX IF NOT EXISTS field_problem_reports_field_open_idx
  ON public.field_problem_reports(field_id,status,created_at DESC);
CREATE INDEX IF NOT EXISTS field_problem_reports_author_idx
  ON public.field_problem_reports(author_id,client_created_at DESC);
ALTER TABLE public.field_problem_reports ENABLE ROW LEVEL SECURITY;

-- Save author and server-receipt timestamp based on authenticated membership.
-- SECURITY INVOKER: no elevated lookup of auth.users or bypass of membership RLS.
CREATE OR REPLACE FUNCTION app_private.stamp_field_problem_report()
RETURNS trigger LANGUAGE plpgsql SECURITY INVOKER SET search_path=''
AS $$
DECLARE real_name text;
BEGIN
  IF auth.uid() IS NULL OR NEW.author_id IS DISTINCT FROM auth.uid() THEN
    RAISE EXCEPTION 'Author mismatch' USING ERRCODE='42501';
  END IF;
  SELECT m.display_name INTO real_name
  FROM public.field_memberships m
  WHERE m.field_id=NEW.field_id AND m.user_id=auth.uid()
    AND m.approved=true AND m.blocked=false
  LIMIT 1;
  IF real_name IS NULL THEN
    RAISE EXCEPTION 'Inactive membership' USING ERRCODE='42501';
  END IF;
  NEW.author_name:=real_name;
  NEW.created_at:=now();
  RETURN NEW;
END;
$$;
DROP TRIGGER IF EXISTS stamp_field_problem_report ON public.field_problem_reports;
CREATE TRIGGER stamp_field_problem_report BEFORE INSERT
ON public.field_problem_reports FOR EACH ROW
EXECUTE FUNCTION app_private.stamp_field_problem_report();

DROP POLICY IF EXISTS field_problem_report_read ON public.field_problem_reports;
CREATE POLICY field_problem_report_read ON public.field_problem_reports
  FOR SELECT TO authenticated
  USING (app_private.is_member(field_id));
DROP POLICY IF EXISTS field_problem_report_add ON public.field_problem_reports;
CREATE POLICY field_problem_report_add ON public.field_problem_reports
  FOR INSERT TO authenticated
  WITH CHECK (
    author_id=(select auth.uid())
    AND status='open' AND resolved_at IS NULL AND resolved_by IS NULL
    AND app_private.is_member(field_id)
  );
DROP POLICY IF EXISTS field_problem_report_resolve ON public.field_problem_reports;
CREATE POLICY field_problem_report_resolve ON public.field_problem_reports
  FOR UPDATE TO authenticated
  USING (app_private.can_resolve_problem(field_id))
  WITH CHECK (app_private.can_resolve_problem(field_id)
    AND status IN ('open','resolved'));
REVOKE ALL ON TABLE public.field_problem_reports FROM PUBLIC,anon,authenticated;
GRANT SELECT,INSERT ON TABLE public.field_problem_reports TO authenticated;
GRANT UPDATE(status,resolved_at,resolved_by)
  ON TABLE public.field_problem_reports TO authenticated;
-- Trigger is invoked on INSERT but cannot be used as a direct API entrypoint.
REVOKE ALL ON FUNCTION app_private.stamp_field_problem_report() FROM PUBLIC,anon,authenticated;
