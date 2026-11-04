"""Fix duplicate menu entries and return to the actual previous route in wells.
Run after prepare_promysel_v180.py on the generated Flutter source.
"""
from pathlib import Path
import re

menu = Path('lib/features/menu/menu_screen.dart')
s = menu.read_text(encoding='utf-8')
for item in (
    "   _entry(context,Icons.chat_bubble_outline,'Чаты','Личные переписки, группы, Избранное и вложения','/chat'),\n",
    "   _entry(context,Icons.assignment_outlined,'Задания','Личные и общие задания','/tasks'),\n",
):
    assert s.count(item) == 1, 'Menu entry absent or duplicated: ' + item
    s = s.replace(item, '', 1)
menu.write_text(s, encoding='utf-8')

wells = Path('lib/features/areas/wells_hierarchy_screen.dart')
s = wells.read_text(encoding='utf-8')
old = "leading:IconButton(tooltip:'Назад в меню',icon:const Icon(Icons.arrow_back),onPressed:()=>context.go('/menu'))"
new = "leading:IconButton(tooltip:'Назад',icon:const Icon(Icons.arrow_back),onPressed:(){if(context.canPop()){context.pop();}else{context.go('/menu');}})"
assert s.count(old) == 1, 'Expected v1.80 well hierarchy back button not found'
wells.write_text(s.replace(old, new, 1), encoding='utf-8')

pub = Path('pubspec.yaml')
s = pub.read_text(encoding='utf-8')
s, n = re.subn(r'(?m)^version:\s*1\.80\.0\+186\s*$', 'version: 1.81.0+187', s, count=1)
assert n == 1, 'Unexpected package version'
pub.write_text(s, encoding='utf-8')
print('v1.81: compact menu and wells back navigation regression fix applied')
