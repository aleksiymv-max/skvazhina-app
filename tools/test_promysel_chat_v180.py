from pathlib import Path
app=Path('lib/app/app.dart').read_text()
ui=Path('lib/features/chat/promysel_chat_screen.dart').read_text()
service=Path('lib/core/services/promysel_chat_service.dart').read_text()
schedule=Path('lib/features/organization/work_schedule_screen.dart').read_text()
pad=Path('lib/features/walk/pad_walk_card_screen.dart').read_text()
checks={
 'chat_branch':"GoRoute(path: '/chat'" in app,
 'chat_from_menu':"'Чаты'" in Path('lib/features/menu/menu_screen.dart').read_text(),
 'chat_bottom':"7=>3" in app and 'PromyselChatUnread.instance' in app,
 'group_and_favorites':"_create('saved')" in ui and "_create('group'" in ui,
 'messages_crud':'changeMessage(' in service and 'deleteMessage(' in service,
 'media_signed_url':"'/rooms/$room/upload'" in service and 'http.put' in service,
 'voice_record':'AudioRecorder()' in ui and 'pickVideo' in ui,
 'mute_sound':'soundEnabled' in ui and 'muted' in ui,
 'cache_clear':'imageCache.clear()' in ui,
 'work_rest_leave':"_legend(Colors.blue.shade100,'Отдых')" in schedule and "_=>Colors.blue.shade100" in schedule and "_legend(Colors.red,'Событие')" not in schedule,
 'compact_pad':"const SizedBox(height:8),SizedBox(width:double.infinity,child:FilledButton.icon" in pad,
 'back_to_menu':all("onPressed:()=>context.go('/menu')" in Path(x).read_text() for x in [
   'lib/features/history/history_screen.dart','lib/features/organization/profile_screen.dart',
   'lib/features/areas/wells_hierarchy_screen.dart','lib/features/tasks/tasks_screen.dart']),
}
for k,v in checks.items():print(f'{k}: {"OK" if v else "FAILED"}')
assert all(checks.values()),[k for k,v in checks.items() if not v]