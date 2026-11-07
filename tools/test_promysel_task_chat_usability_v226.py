#!/usr/bin/env python3
"""Static generated-source regression for usability fixes, both Web and Android."""
from pathlib import Path
t=Path("lib/features/tasks/tasks_screen.dart").read_text()
c=Path("lib/features/chat/promysel_chat_screen.dart").read_text()
p=Path("lib/features/tasks/task_photo_widgets.dart").read_text()
tests={
 "operators allowed to create tasks":"final canIssue=u.canCreateTask;" in t,
 "task roster does not exclude the author":"x.role!=UserRole.admin&&x.id!=me.id" not in t,
 "approved field-scoped roster used":"session.approvedWorkers.where(" in t,
 "roster network refresh requested":"session.refreshWorkers()" in t,
 "live roster update when dialog open":"ListenableBuilder(\n     listenable:session" in t,
 "current field enforced upstream":"approvedWorkers" in t and "userFields" in Path("lib/core/services/session_service.dart").read_text(),
 "live work status only when known":"!session.workPresence.containsKey(x.id)" in t,
 "non-working known staff not silently included":"session.isAtWork(x.id)||!session.workPresence.containsKey(x.id)" in t,
 "task recipient cannot be missing on existing refreshed list":"if(available.isNotEmpty&&!available.any" in t,
 "chat list updated when visible at 18 seconds":"tick=Timer.periodic(const Duration(seconds:18),(_){" in c,
 "chat list no old 120 seconds":"tick=Timer.periodic(const Duration(seconds:120)" not in c,
 "chat images not cropped":"fit:BoxFit.cover" not in c and "fit:BoxFit.contain" in c,
 "keyboard follows latest message":"with WidgetsBindingObserver{" in c and "didChangeMetrics()" in c and
     "focusNode:_messageFocus,onTap:_keepLatestVisible" in c and "list.position.maxScrollExtent" in c,
 "keyboard observer removed":"WidgetsBinding.instance.removeObserver(this);_messageFocus.dispose();" in c,
 "task photos preserve proportions":"Image.memory(photo.bytes,width:75,height:75,fit:BoxFit.contain)" in p and
     "Image.network(signed,fit:BoxFit.contain," in p,
 "no destructive operations":not any(x in t+c+p for x in ["TRUNCATE TABLE","DELETE FROM public."])
}
for name,ok in tests.items():print(("PASS " if ok else "FAIL ")+name)
assert all(tests.values()),"v2.26 usability regressions"
