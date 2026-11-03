"""Static fail-closed checks for the STAGING-ONLY task registry proposal.

This does not execute PostgreSQL, RLS, Storage, or authenticated E2E tests.
Those tests are mandatory before any production migration or merge.
"""
from pathlib import Path
import re

sql_path = Path(__file__).resolve().parents[1] / "supabase/staging/20261102_task_registry_evidence_review_only.sql"
sql = sql_path.read_text(encoding="utf-8")
low = sql.lower()

def require(condition, message):
    if not condition:
        raise AssertionError(message)

def function_body(name):
    pattern = r"create function " + re.escape(name) + r"\([^)]*\).*?as \$\$(.*?)\$\$;"
    match = re.search(pattern, sql, re.S | re.I)
    require(match is not None, "Missing function: " + name)
    return match.group(1)

require("create table public.work_task_assignees" in low, "Explicit common-task recipients missing")
require("foreign key(field_id,task_id) references public.work_tasks(field_id,id)" in low,
        "Recipients must reference a real task in the same field")
require("foreign key(user_id,field_id) references public.field_memberships(user_id,field_id)" in low,
        "Recipients must be field members")
require("alter table public.work_task_assignees enable row level security" in low, "Recipients RLS missing")
require("revoke insert on public.work_task_assignees from authenticated" in low,
        "Clients must not insert recipients directly")
require("grant execute on function public.promysel_assign_task_assignee(text,text,uuid)" in low,
        "Assignment must use authenticated RPC")
assign = function_body("public.promysel_assign_task_assignee")
require(assign.index("for update;") < assign.index("insert into public.work_task_assignees"),
        "Assignment must lock task before inserting recipient")
require("t.status<>'active'" in assign and "m.approved and not m.blocked" in assign,
        "Assignment must check status and membership")
require("m.field_id=work_task_assignees.field_id" in low and
        "m.user_id=work_task_assignees.user_id" in low,
        "Recipient membership must use qualified field and user identifiers")
require("t.field_id=work_task_assignees.field_id" in low and
        "t.id=work_task_assignees.task_id" in low,
        "Recipient task lookup must use qualified field and task identifiers")
require("m.approved and not m.blocked" in low, "Recipient must be approved and unblocked")

for name in ("app_private.can_view_task", "app_private.can_attach_task"):
    body = function_body(name)
    require("from public.work_task_assignees a" in body,
            name + " must check explicit recipients for common tasks")
    require("a.field_id=t.field_id and a.task_id=t.id" in body,
            name + " must bind recipients to both field and task")
    require("a.user_id=(select auth.uid())" in body,
            name + " must bind recipients to the authenticated user")
    require("and app_private.can_walk(p_field)" in body,
            name + " must enforce current walk role")

complete = function_body("public.promysel_complete_task")
require(complete.index("for update;") < complete.index("app_private.can_attach_task(p_field,p_task)"),
        "Completion must lock the task BEFORE checking assignment (revoke race)")

review = function_body("public.promysel_review_task")
require("not app_private.can_manage_tasks(p_field)" in review,
        "Former authors who lost task management privileges must not review")
require("t.created_by<>v_actor" in review and "member_role(p_field)<>'shopChief'" in review,
        "Only current author or chief may review")

require("foreign key(field_id,task_id) references public.work_tasks(field_id,id)" in low,
        "Evidence must refer to canonical tasks")
require("public,file_size_limit,allowed_mime_types" in low and
        "values('promysel-task-evidence','promysel-task-evidence',false" in low,
        "Evidence Storage bucket must be private")
require("grant select,insert on public.task_evidence to authenticated" in low,
        "Evidence table must not allow client update/delete")
require("grant execute on function public.promysel_review_task(text,text,boolean,text) to authenticated" in low,
        "Task review must be authenticated")
require("create policy promysel_task_photo_upload" in low and
        "app_private.can_attach_task(e.field_id,e.task_id)" in low,
        "Storage upload must verify task authorization")
require(low.count("delete from public.work_task_assignees") == 1,
        "Only the audited task assignee revocation may delete rows")
sql_without_audited_revocation = low.replace("delete from public.work_task_assignees", "", 1)
require(not re.search(r"\b(drop table|truncate table|delete from public\.)\b",
                      sql_without_audited_revocation),
        "Staging proposal unexpectedly contains destructive statements")
require(sql_path.parent.name == "staging", "SQL must remain outside auto-deployed migrations")

require("create table public.work_task_assignee_events" in low,
        "Revocation audit table missing")
revoke_body = function_body("public.promysel_revoke_task_assignee")
require("app_private.can_manage_tasks(p_field)" in revoke_body,
        "Revocation must require current manager")
require("delete from public.work_task_assignees" in revoke_body,
        "Revocation must actually remove recipient")
require("insert into public.work_task_assignee_events" in revoke_body,
        "Revocation must create an audit event")
require("grant execute on function public.promysel_revoke_task_assignee(text,text,uuid)" in low,
        "Revocation must use authenticated RPC")
require("grant select on public.work_task_assignee_events to authenticated" in low,
        "Audit must be read-only to clients")

print("PASS: staging-only static task audience, role, evidence and Storage guards")
print("NOT TESTED: PostgreSQL parsing, actual RLS, Storage upload, two-account E2E, backfill, rollback")
