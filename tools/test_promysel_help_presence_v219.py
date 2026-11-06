#!/usr/bin/env python3
"""Regressions: midnight presence continuity and simple, safe user help."""
from pathlib import Path
session=Path('lib/core/services/session_service.dart').read_text(encoding='utf-8')
about=Path('lib/features/menu/about_screen.dart').read_text(encoding='utf-8')
server=(Path(__file__).resolve().parents[1]/'supabase/functions/promysel-compat/index.ts').read_text(encoding='utf-8')
presence=server[server.index('if(route==="/v1/presence"&&req.method==="GET")'):
                server.index('const presenceRoute=route.match')]
releases=about[about.index('class _ReleasePage'):about.index('class _CheckIssue')]
checks={
 'midnight does not reset statuses':
   'if(day!=_presenceDay){_presenceDay=day;_presenceLastRead=null;}' in session and
   'workPresence.clear();_presenceLastRead=null;' not in session,
 'refresh still happens on new day':
   'void _checkPresenceDay()' in session and '_presenceLastRead=null;' in session,
 'server returns last explicit status on or before day':
   '.lte("work_day",day)' in presence and '.order("work_day",{ascending:false})' in presence and
   'if(id&&!latest.has(id))latest.set(id,row as J);' in presence,
 'server scoping and authorization retained':
   '!administrator&&!canField(fid)' in presence and '.eq("field_id",fid)' in presence,
 'server response compatible with old clients':
   'id:x.user_id,atWork:x.is_working,updatedAt:x.updated_at' in presence,
 'no midnight database rewrites':
   '.upsert(' not in presence and '.delete(' not in presence,
 'version only': "Версия v2.21" in releases and
   "История обновлений" not in releases and "_Section('v2." not in releases,
 'one combined action button':about.count('FilledButton.icon(')==1 and
   'OutlinedButton.icon(' not in about and 'await sync.syncNow(force:true);' in about,
 'three checks on one press':
   'prefs.getKeys();' in about and "Uri.parse('$_base/health')" in about and
   'await sync.syncNow(force:true);' in about,
 'errors include code, type and description':
   "_detail('Код ошибки',issue.code)" in about and
   "_detail('Тип ошибки',issue.type)" in about and
   "SelectableText(issue.description)" in about,
 'manual complete':all(section in about for section in [
   'Обход скважин','История замеров и тренды','Задания и фотографии',
   'Персонал и статус работы','Работа без интернета',
   'Участки, кусты и скважины','Чаты','Безопасность работы']),
 'expansion card corners clipped':
   'clipBehavior: Clip.antiAlias' in about and
   'dividerColor: Colors.transparent' in about and
   'collapsedShape: tileShape' in about and 'shape: tileShape' in about,
 'no destructive troubleshooting':all(bad not in about for bad in
   ['deleteDatabase(', 'localStorage.clear(', 'clearPersistedSession('])
}
for key,good in checks.items(): print(('PASS ' if good else 'FAIL ')+key)
assert all(checks.values()),'v2.19 help and presence contract failed'
