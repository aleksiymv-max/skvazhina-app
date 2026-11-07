#!/usr/bin/env python3
"""One-time read-only generated-source inspection; prints only source fragments, not user data."""
from pathlib import Path
def show(path, needles, before=180, after=2500):
 s=Path(path).read_text()
 print('=== FILE',path,'bytes',len(s))
 for needle in needles:
  p=s.find(needle)
  print('=== NEEDLE',repr(needle),'pos',p)
  if p>=0:print(s[max(0,p-before):p+after])
show('lib/features/tasks/tasks_screen.dart',[
 'bool get canIssue','final canIssue','Future<void> _create()','approvedWorkers',
 'final me=SessionService.instance.currentUser','final people=', 'onPressed:_create'])
show('lib/core/services/session_service.dart',[
 'approvedWorkers', 'userFields', 'Future<void> load', 'Future<void> refresh',
 'working', 'workStatus','presence'])
show('lib/core/models/user.dart',['canIssue','canCreateTask','canAssignTask','canCreateStructure'])
show('lib/features/chat/promysel_chat_screen.dart',[
 'class _PromyselChatScreenState','Future<void> _load({bool silent=false})',
 'class _PromyselChatRoomScreenState','@override Widget build(BuildContext context){\n    final visible=',"kind=='image'",'SafeArea(top:false'])
show('lib/core/services/promysel_chat_service.dart',['Future<List<Map<String,dynamic>>> rooms()','Future<Map<String,dynamic>> call('])
