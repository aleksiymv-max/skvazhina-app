#!/usr/bin/env python3
"""v2.13: generated Flutter network-source inventory. Read only; no secrets."""
from pathlib import Path
import re
paths={
  "session":"lib/core/services/session_service.dart",
  "sync":"lib/core/services/sync_service.dart",
  "chat":"lib/core/services/promysel_chat_service.dart",
  "chat_screen":"lib/features/chat/promysel_chat_screen.dart",
  "registration":"lib/core/services/registration_service.dart",
  "photos":"lib/core/services/task_photo_service.dart",
  "notifications":"lib/core/services/task_notification_service.dart",
}
patterns=[
  r"Timer\.periodic",r"Duration\(seconds:",r"syncNow\(",
  r"refreshWorkers\(",r"refreshPresence\(",r"refreshFields\(",
  r"ensureFreshToken\(",r"getUser\(",r"\.get\(",r"\.post\(",
  r"\.subscribe\(",r"\.cancel\(",r"fetchMessages\(",
  r"poll",r"Timer\(",r"Future\.delayed\(",r"persist\(",
  r"refreshNotifications\(",r"refreshPending\(",
]
for name,path in paths.items():
 p=Path(path)
 if not p.exists():
  print("MISSING",name,path);continue
 s=p.read_text(encoding="utf8")
 print("\nFILE",name,len(s),"bytes",s.count("\n")+1,"lines")
 lines=s.splitlines()
 for pattern in patterns:
  matches=[(i+1,line.strip()) for i,line in enumerate(lines) if re.search(pattern,line,re.I)]
  if not matches:continue
  print("MATCH",pattern,len(matches))
  for lineno,line in matches[:8]:
   line=line.replace("Bearer ","Bearer [redacted] ")
   print(lineno,line[:300])
print("PASS: source inventory complete")
