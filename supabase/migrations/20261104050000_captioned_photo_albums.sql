-- One captioned album message with up to ten photographs; existing history remains intact.
alter table public.promysel_chat_messages add column if not exists attachments jsonb not null default '[]'::jsonb;
alter table public.promysel_chat_messages drop constraint if exists promysel_chat_messages_kind_check;
alter table public.promysel_chat_messages add constraint promysel_chat_messages_kind_check
 check (kind in ('text','image','video','voice','document','album'));
alter table public.promysel_chat_messages drop constraint if exists promysel_chat_messages_check;
alter table public.promysel_chat_messages add constraint promysel_chat_messages_check check(
 (kind='text' and length(trim(body))>0 and attachment_path is null)
 or (kind='album' and attachment_path is null and jsonb_typeof(attachments)='array'
     and jsonb_array_length(attachments) between 1 and 10)
 or (kind in ('image','video','voice','document') and attachment_path is not null));
