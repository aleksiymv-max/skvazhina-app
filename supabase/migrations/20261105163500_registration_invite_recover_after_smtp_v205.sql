-- v2.05.1: Configuration errors can be retried after a brief cooldown once SMTP is installed.
create or replace function public.promysel_claim_registration_invitation(
 p_request_id bigint,p_actor uuid
) returns jsonb
language plpgsql security definer set search_path='' as $$
declare
 v_request public.registration_requests%rowtype;
 v_job public.promysel_registration_invitation_jobs%rowtype;
 v_next timestamptz;
 v_retry timestamptz;
 v_admin boolean:=false;
 v_chief boolean:=false;
begin
 select * into v_request from public.registration_requests r
   where r.id=p_request_id for update;
 if not found or v_request.state<>'approved' then
   raise exception 'Заявка ещё не согласована';
 end if;
 select coalesce(u.raw_app_meta_data->>'system_admin'='true',false)
   into v_admin from auth.users u where u.id=p_actor;
 select exists(
   select 1 from public.field_memberships m
   where m.user_id=p_actor and m.field_id=v_request.approved_field_id
     and m.role='shopChief' and m.approved and not m.blocked
 ) into v_chief;
 if not (v_admin or v_chief) then
   raise exception 'Нет права отправлять приглашение';
 end if;
 insert into public.promysel_registration_invitation_jobs(request_id)
   values(p_request_id) on conflict(request_id) do nothing;
 select * into v_job from public.promysel_registration_invitation_jobs j
   where j.request_id=p_request_id for update;
 if v_request.invitation_sent_at is not null or v_job.status='sent' then
   return jsonb_build_object('canSend',false,'status','sent');
 end if;
 if v_job.status='accepted' and v_job.accepted_user_id is not null then
   return jsonb_build_object('canSend',false,'status','accepted',
     'acceptedUserId',v_job.accepted_user_id);
 end if;
 if v_job.status='action_required' and v_job.next_attempt_at>now() then
   return jsonb_build_object('canSend',false,'status','action_required');
 end if;
 if v_job.locked_until is not null and v_job.locked_until>now() then
   return jsonb_build_object('canSend',false,'status','sending',
     'nextRetryAt',v_job.locked_until);
 end if;
 -- A global mail budget prevents a flood of rate-limited invitations.
 insert into public.promysel_invitation_mail_gate(key)
 values('supabase-auth') on conflict(key) do nothing;
 select g.next_available_at into v_next
   from public.promysel_invitation_mail_gate g
   where g.key='supabase-auth' for update;
 v_retry:=greatest(coalesce(v_next,now()),v_job.next_attempt_at);
 if v_retry>now() then
   return jsonb_build_object('canSend',false,'status','queued',
     'nextRetryAt',v_retry,'attempts',v_job.attempts);
 end if;
 update public.promysel_invitation_mail_gate
   set next_available_at=now()+interval '31 minutes',updated_at=now()
   where key='supabase-auth';
 update public.promysel_registration_invitation_jobs
   set status='sending',attempts=attempts+1,
       last_attempt_at=now(),locked_until=now()+interval '90 seconds',
       next_attempt_at=now()+interval '31 minutes',
       last_error_code=null,updated_at=now()
   where request_id=p_request_id;
 return jsonb_build_object('canSend',true,'status','sending',
     'attempts',v_job.attempts+1);
end $$;

create or replace function public.promysel_record_registration_invitation(
 p_request_id bigint,p_actor uuid,p_status text,p_user_id uuid default null,
 p_error_code text default null
) returns jsonb
language plpgsql security definer set search_path='' as $$
declare
 v_job public.promysel_registration_invitation_jobs%rowtype;
 v_request public.registration_requests%rowtype;
 v_delay interval;
 v_code text:=left(coalesce(p_error_code,''),90);
 v_admin boolean:=false;v_chief boolean:=false;
begin
 select * into v_request from public.registration_requests r
   where r.id=p_request_id for update;
 if not found or v_request.state<>'approved' then
   raise exception 'Заявка не согласована';
 end if;
 select coalesce(u.raw_app_meta_data->>'system_admin'='true',false)
   into v_admin from auth.users u where u.id=p_actor;
 select exists(select 1 from public.field_memberships m
   where m.user_id=p_actor and m.field_id=v_request.approved_field_id
   and m.role='shopChief' and m.approved and not m.blocked)
   into v_chief;
 if not(v_admin or v_chief) then raise exception 'Нет доступа к приглашению';end if;
 select * into v_job from public.promysel_registration_invitation_jobs j
   where j.request_id=p_request_id for update;
 if not found then raise exception 'Очередь отправки не найдена';end if;
 if p_status='accepted' then
   if p_user_id is null then raise exception 'Не указан получатель приглашения';end if;
   update public.promysel_registration_invitation_jobs
   set status='accepted',accepted_user_id=p_user_id,
     locked_until=null,last_error_code=null,updated_at=now()
   where request_id=p_request_id;
 elsif p_status='sent' then
   update public.promysel_registration_invitation_jobs
   set status='sent',sent_at=now(),locked_until=null,
       next_attempt_at=now(),updated_at=now()
   where request_id=p_request_id and accepted_user_id is not null;
 elsif p_status in('retry','action_required') then
   v_delay:=case when v_code in('over_email_send_rate_limit','email_rate_limit')
       then interval '65 minutes'
     when p_status='action_required' then interval '15 minutes'
     else interval '15 minutes' end;
   update public.promysel_registration_invitation_jobs
   set status=p_status,locked_until=null,last_error_code=v_code,
       next_attempt_at=now()+v_delay,updated_at=now()
   where request_id=p_request_id and status<>'accepted';
   if v_code in('over_email_send_rate_limit','email_rate_limit') then
     update public.promysel_invitation_mail_gate
     set next_available_at=greatest(next_available_at,now()+interval '65 minutes'),
       updated_at=now()
     where key='supabase-auth';
   end if;
 else
   raise exception 'Недопустимый статус отправки';
 end if;
 return jsonb_build_object('status',p_status);
end $$;
