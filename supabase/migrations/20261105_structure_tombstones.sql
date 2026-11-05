-- Promysel v1.94: keep authorized structure deletions durable across offline
-- devices. No existing data is removed or changed by this migration.
CREATE TABLE IF NOT EXISTS public.promysel_structure_tombstones (
  field_id text NOT NULL REFERENCES public.oil_fields(id) ON DELETE RESTRICT,
  kind text NOT NULL CHECK (kind IN ('areas','pads','wells')),
  entity_id text NOT NULL CHECK (length(entity_id)>0 AND length(entity_id)<=180),
  actor_id uuid REFERENCES auth.users(id) ON DELETE SET NULL,
  deleted_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (field_id,kind,entity_id)
);
ALTER TABLE public.promysel_structure_tombstones ENABLE ROW LEVEL SECURITY;
-- Only Edge Functions using the server-side service_role may manage markers.
REVOKE ALL ON TABLE public.promysel_structure_tombstones FROM anon, authenticated;
COMMENT ON TABLE public.promysel_structure_tombstones IS
  'Immutable per-field deletion markers for removed areas, pads and wells. Do not delete historical measurements.';
