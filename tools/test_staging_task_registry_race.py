"""Deterministic task revocation/completion race on disposable PostgreSQL only.

Requires the synthetic fixture, staging SQL, and PG* environment variables
configured by the CI service. No production credentials or real users.
"""
from pathlib import Path
import subprocess
import tempfile

CHIEF = "00000000-0000-0000-0000-000000000001"
OPERATOR = "00000000-0000-0000-0000-000000000003"
ROOT = Path(__file__).resolve().parents[1]


def run_sql(sql: str, *, check: bool = True):
    result = subprocess.run(
        ["psql", "-X", "-q", "-A", "-t", "-v", "ON_ERROR_STOP=1", "-c", sql],
        text=True, capture_output=True, timeout=20,
    )
    if check and result.returncode:
        raise AssertionError(result.stderr)
    return result


run_sql(f"""
set role authenticated;
select set_config('request.jwt.claim.sub','{CHIEF}',false);
insert into public.work_tasks(field_id,id,title,target_type,target_id,created_by)
values('field-a','area-race','Concurrent revocation test','area','area-a','{CHIEF}');
insert into public.work_task_assignees(field_id,task_id,user_id)
values('field-a','area-race','{OPERATOR}');
""")

# Hold the task row lock, then revoke while a completion request waits.
# The pre-fix RPC checked permission BEFORE taking this lock and could
# complete after the assignment had already been revoked.
with tempfile.TemporaryDirectory() as temp:
    chief_script = Path(temp) / "chief.sql"
    chief_script.write_text(f"""
\\set ON_ERROR_STOP on
begin;
set role authenticated;
select set_config('request.jwt.claim.sub','{CHIEF}',false);
select id from public.work_tasks where field_id='field-a' and id='area-race' for update;
\\echo TASK_LOCKED
select pg_sleep(3);
select public.promysel_revoke_task_assignee('field-a','area-race','{OPERATOR}');
commit;
""", encoding="utf-8")
    chief = subprocess.Popen(
        ["psql", "-X", "-q", "-A", "-t", "-f", str(chief_script)],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        bufsize=1,
    )
    try:
        assert chief.stdout is not None
        locked = False
        for _ in range(10):
            line = chief.stdout.readline()
            if not line:
                break
            if "TASK_LOCKED" in line:
                locked = True
                break
        assert locked, "Chief failed to acquire task lock"
        operator = run_sql(f"""
set role authenticated;
select set_config('request.jwt.claim.sub','{OPERATOR}',false);
select public.promysel_complete_task('field-a','area-race');
""", check=False)
        chief_out, chief_err = chief.communicate(timeout=20)
        assert chief.returncode == 0, f"Chief revoke failed: {chief_err} {chief_out}"
        assert operator.returncode != 0, "Revoked operator completed a task after revocation"
        assert "Not allowed to complete this task" in operator.stderr, operator.stderr
    finally:
        if chief.poll() is None:
            chief.kill()
            chief.communicate()

result = run_sql("""
select t.status || ':' ||
  (select count(*) from public.work_task_assignees a
   where a.field_id=t.field_id and a.task_id=t.id) || ':' ||
  (select count(*) from public.work_task_events e
   where e.field_id=t.field_id and e.task_id=t.id) || ':' ||
  (select count(*) from public.work_task_assignee_events e
   where e.field_id=t.field_id and e.task_id=t.id)
from public.work_tasks t where t.field_id='field-a' and t.id='area-race';
""")
assert "active:0:0:1" in result.stdout, result.stdout
print("PASS: concurrent revocation wins; stale completion rejected without event")
