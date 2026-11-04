-- Recording metadata and optional, server-side transcription. No existing media is deleted.
alter table public.promysel_chat_messages add column if not exists waveform jsonb not null default '[]'::jsonb;
alter table public.promysel_chat_messages add column if not exists duration_ms integer;
alter table public.promysel_chat_messages add column if not exists transcript text;
alter table public.promysel_chat_messages drop constraint if exists promysel_chat_messages_kind_check;
alter table public.promysel_chat_messages add constraint promysel_chat_messages_kind_check
 check (kind in ('text','image','video','video_note','voice','document','album'));
alter table public.promysel_chat_messages drop constraint if exists promysel_chat_messages_check;
alter table public.promysel_chat_messages add constraint promysel_chat_messages_check check(
 (kind='text' and length(trim(body))>0 and attachment_path is null)
 or (kind='album' and attachment_path is null and jsonb_typeof(attachments)='array'
     and jsonb_array_length(attachments) between 1 and 10)
 or (kind in ('image','video','video_note','voice','document') and attachment_path is not null)
);
alter table public.promysel_chat_messages drop constraint if exists promysel_chat_waveform_check;
alter table public.promysel_chat_messages add constraint promysel_chat_waveform_check check(
 jsonb_typeof(waveform)='array' and jsonb_array_length(waveform)<=65);
alter table public.promysel_chat_messages drop constraint if exists promysel_chat_duration_check;
alter table public.promysel_chat_messages add constraint promysel_chat_duration_check check(
 duration_ms between 0 and 120000);
alter table public.promysel_chat_messages drop constraint if exists promysel_chat_transcript_check;
alter table public.promysel_chat_messages add constraint promysel_chat_transcript_check check(
 transcript is null or length(transcript)<=12000);
comment on column public.promysel_chat_messages.waveform is 'Amplitude samples actually measured during microphone recording';
comment on column public.promysel_chat_messages.transcript is 'Only user-initiated server-side speech recognition writes this field';
