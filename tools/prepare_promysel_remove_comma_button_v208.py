#!/usr/bin/env python3
"""v2.08: remove decorative comma buttons while keeping decimal comma input."""
from pathlib import Path
p=Path('lib/features/wells/well_screen.dart')
s=p.read_text(encoding='utf-8')
old="""      suffixIconConstraints:const BoxConstraints(minWidth:30,minHeight:34),
      suffixIcon:integer?null:IconButton(
        visualDensity:VisualDensity.compact,padding:EdgeInsets.zero,
        constraints:const BoxConstraints(minWidth:30,minHeight:34),
        tooltip:'Вставить запятую',onPressed:enabled?
          ()=>PromyselDecimalInput.insertComma(c):null,
        icon:const Text(',',style:TextStyle(fontSize:23,fontWeight:FontWeight.bold)),
      ),
"""
assert s.count(old)==1, 'Expected one numeric field suffix comma control'
s=s.replace(old,'',1)
assert 'inputFormatters:[integer?PromyselDecimalInput.integer:PromyselDecimalInput.decimal]' in s
assert 'suffixText:unit' in s
p.write_text(s,encoding='utf-8')
print('PASS v2.08: no side comma button, decimal keyboard and comma parser preserved')
