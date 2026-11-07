-- Additive chat reactions. All user requests go through the existing authenticated Edge API.
-- No historical messages, uploads, rooms, permissions or media are altered.
CREATE TABLE IF NOT EXISTS public.promysel_chat_reactions (
  message_id uuid NOT NULL REFERENCES public.promysel_chat_messages(id) ON DELETE CASCADE,
  room_id uuid NOT NULL REFERENCES public.promysel_chat_rooms(id) ON DELETE CASCADE,
  user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE RESTRICT,
  emoji text NOT NULL CHECK (emoji IN ('👍','❤️','😂','😮','😢','👏')),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (message_id,user_id)
);
CREATE INDEX IF NOT EXISTS promysel_chat_reactions_room_idx
  ON public.promysel_chat_reactions (room_id,message_id);
ALTER TABLE public.promysel_chat_reactions ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.promysel_chat_reactions FROM PUBLIC,anon,authenticated;
GRANT SELECT,INSERT,UPDATE,DELETE ON public.promysel_chat_reactions TO service_role;
-- The function authorizes room membership and message visibility on every request.
