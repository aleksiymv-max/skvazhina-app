-- v2.05: approval decision is independent from email delivery.
-- Only Supabase service_role can read/write invitation jobs.
-- Existing approved but undelivered invitations are queued without sending mail.
begin;
create table if not exists public.promysel_registration_invitation_jobs(
 request_id bigint primary key references public.registration_requests(id) on delete cascade,
 status text not null default 'queued'
   check(status in('queued','sending','retry','accepted','sent','action_required')),
 attempts int not null default 0 check(attempts between 0 and 100),
 next_attempt_at timestamptz not null default now(),
 locked_until timestamptz,
 accepted_user_id uuid,
 last_error_code text,
 last_attempt_at timestamptz,
 sent_at timestamptz,
 updated_at timestamptz not null default now()
);
create index if not exists promysel_registration_invitation_jobs_due_idx
 on public.promysel_registration_invitation_jobs(next_attempt_at,request_id)
 where status in ('queued','retry','sending');
alter table public.promysel_registration_invitation_jobs enable row level security;
revoke all on public.promysel_registration_invitation_jobs from public,anon,authenticated;
grant select,insert,update on public.promysel_registration_invitation_jobs to service_role;

create table if not exists public.promysel_invitation_mail_gate(
 key text primary key,
 next_available_at timestamptz not null default now(),
 updated_at timestamptz not null default now()
);
alter table public.promysel_invitation_mail_gate enable row level security;
revoke all on public.promysel_invitation_mail_gate from public,anon,authenticated;
grant select,insert,update on public.promysel_invitation_mail_gate to service_role;
insert into public.promysel_invitation_mail_gate(key,next_available_at)
 values('supabase-auth',now()) on conflict(key) do nothing;

create or replace function app_private.promysel_queue_registration_invite_v205()
returns trigger language plpgsql security definer set search_path='' as $$
begin
 if new.state='approved' then
   insert into public.promysel_registration_invitation_jobs(request_id,status,next_attempt_at,sent_at)
   values(new.id,case when new.invitation_sent_at is null then 'queued' else 'sent' end,
     now(),new.invitation_sent_at)
   on conflict(request_id) do update
   set status=case when new.invitation_sent_at is not null then 'sent'
                   else public.promysel_registration_invitation_jobs.status end,
       sent_at=coalesce(new.invitation_sent_at,public.promysel_registration_invitation_jobs.sent_at),
       updated_at=now();
 end if;
 return new;
end $$;
drop trigger if exists promysel_registration_invite_queue_v205 on public.registration_requests;
create trigger promysel_registration_invite_queue_v205
after insert or update of state,invitation_sent_at on public.registration_requests
for each row execute function app_private.promysel_queue_registration_invite_v205();

insert into public.promysel_registration_invitation_jobs(request_id,status,next_attempt_at,sent_at)
select r.id,
 case when r.invitation_sent_at is not null then 'sent' else 'queued' end,
 now(),r.invitation_sent_at
from public.registration_requests r where r.state='approved'
on conflict(request_id) do nothing;

-- One database transaction reserves one invitation attempt, even when two
-- chiefs click simultaneously. All actual mail calls are made AFTER this RPC.
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
 if v_job.status='action_required' then
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
revoke all on function public.promysel_claim_registration_invitation(bigint,uuid)
 from public,anon,authenticated;
grant execute on function public.promysel_claim_registration_invitation(bigint,uuid)
 to service_role;

-- Email delivery is a separate operation from employee approval.
-- Reserve ACCEPTED status when a provider confirms dispatch; mark SENT only
-- after the employee's membership is finalized by the existing audited RPC.
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
     when p_status='action_required' then interval '1 day'
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
revoke all on function public.promysel_record_registration_invitation(bigint,uuid,text,uuid,text)
 from public,anon,authenticated;
grant execute on function public.promysel_record_registration_invitation(bigint,uuid,text,uuid,text)
 to service_role;

commit;