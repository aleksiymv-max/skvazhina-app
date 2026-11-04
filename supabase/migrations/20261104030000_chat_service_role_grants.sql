-- Chat API writes use the verified service_role client, never the untrusted client.
-- The original chat migration revoked PUBLIC permissions; service_role needs explicit grants.
grant select, insert, update, delete on table
  public.promysel_chat_rooms,
  public.promysel_chat_members,
  public.promysel_chat_messages
to service_role;
revoke all on table
  public.promysel_chat_rooms,
  public.promysel_chat_members,
  public.promysel_chat_messages
from anon, authenticated;
-- RLS remains enabled, and service-role credentials are never exposed to Flutter clients.
