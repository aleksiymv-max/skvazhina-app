-- Permanent structure tombstones preserve chief-authorized deletions across
-- device reconnections and prevent stale state snapshots from reviving objects.
-- This migration is additive: no areas, pads, wells or measurements are deleted.
CREATE TABLE IF NOT EXISTS public.promysel_structure_tombstones (
  field_id text NOT NULL REFERENCES public.oil_fields(id) ON DELETE CASCADE,
  kind text NOT NULL CHECK(kind IN ('areas','pads','wells')),
  entity_id text NOT NULL CHECK(length(entity_id) BETWEEN 1 AND 180),
  actor_id uuid NULL REFERENCES auth.users(id) ON DELETE SET NULL,
  deleted_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY(field_id,kind,entity_id)
);
ALTER TABLE public.promysel_structure_tombstones ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.promysel_structure_tombstones FROM anon,authenticated;
GRANT SELECT,INSERT ON public.promysel_structure_tombstones TO service_role;
COMMENT ON TABLE public.promysel_structure_tombstones IS 'Chief-authorized permanent deletion ledger for areas, pads and wells. Measurement history preserved.';
