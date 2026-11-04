"""Static navigation/menu checks on generated Flutter source."""
from pathlib import Path
menu = Path('lib/features/menu/menu_screen.dart').read_text(encoding='utf-8')
wells = Path('lib/features/areas/wells_hierarchy_screen.dart').read_text(encoding='utf-8')
home = Path('lib/features/home/home_screen.dart').read_text(encoding='utf-8')
app = Path('lib/app/app.dart').read_text(encoding='utf-8')
assert "_entry(context,Icons.chat_bubble_outline,'Чаты'" not in menu
assert "_entry(context,Icons.assignment_outlined,'Задания'" not in menu
assert "_entry(context,Icons.oil_barrel_outlined,'Скважины'" in menu
assert "context.push('/wells?from=home')" in home, 'Home origin must be preserved'
assert "'/wells?from=menu'" in menu, 'Menu origin must be preserved'
assert "if(context.canPop()){context.pop();}else{final origin=GoRouterState.of(context).uri.queryParameters['from'];context.go(origin=='home'?'/':'/menu');}" in wells
assert "label:'Чат'" in app and "label:'Задания'" in app
assert "version: 1.81.0+187" in Path('pubspec.yaml').read_text()
print('v1.81 navigation/menu regression checks passed')
