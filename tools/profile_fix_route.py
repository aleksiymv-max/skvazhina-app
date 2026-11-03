from pathlib import Path
p=Path('lib/features/organization/profile_screen.dart')
c=p.read_text()
needle='   ])))));'
assert c.count(needle)==1
p.write_text(c.replace(needle,'   ]))));'))
