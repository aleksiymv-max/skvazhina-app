#!/usr/bin/env python3
"""Read-only source-inspection report: print selected blocks from generated Flutter.
Designed for GitHub Actions logs; no credentials, user data or file mutation.
"""
from pathlib import Path
import re

root=Path('lib')
paths={
  'sync':'core/services/sync_service.dart',
  'app_state':'core/services/app_state_store.dart',
  'tasks':'core/models/work_task.dart',
  'task_ui':'features/tasks/tasks_screen.dart',
  'session':'core/services/session_service.dart',
  'network':'core/network/weak_network.dart'
}
files={kind:(root/path).read_text(encoding='utf-8') for kind,path in paths.items()}
for kind,text in files.items():
    print('FILE',kind,len(text),'bytes',text.count('\n')+1,'lines')
def excerpts(kind,patterns,size=3200):
    content=files[kind]
    for label,search in patterns:
        occurrences=list(re.finditer(re.escape(search),content))
        print('---',kind,label,'matches',len(occurrences),'---')
        for found in occurrences[:2]:
            left=max(0,content.rfind('\n',max(0,found.start()-300)))
            print(content[left:left+size].replace('Bearer ','Bearer [REDACTED] ').replace('service_role','[SERVICE_ROLE_REF]'))
excerpts('sync',[
 ('syncNow','Future<void> syncNow'),
 ('pushState','Future<void> _pushState'),
 ('pull','Future<void> _pull'),
 ('markStateDirty','void markStateDirty'),
 ('stateChanged','void _stateChanged'),
 ('queue retry','_syncAgain'),
],4300)
excerpts('tasks',[
 ('complete','bool complete('),
 ('confirm','bool confirm('),
 ('reject','bool reject('),
],2400)
excerpts('app_state',[
 ('snapshot','Map<String,dynamic> snapshot('),
 ('reconcile','reconcileWithCurrent'),
],1800)
print('PASS generated source inspection completed')
