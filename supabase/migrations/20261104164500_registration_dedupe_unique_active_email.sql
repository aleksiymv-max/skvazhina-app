-- Prevent duplicate live registrations caused by concurrent taps/devices.
-- Rejected applications stay as auditable history and do not block reapplying.
-- The existing duplicate #7 was safely marked rejected after confirming that
-- approved request #8 was linked to the active chief membership.
CREATE UNIQUE INDEX IF NOT EXISTS promysel_registration_one_live_email
ON public.registration_requests (lower(btrim(email)))
WHERE state IN ('pending','approved');
