from pathlib import Path
r=Path.cwd()
def edit(rel,fn):
 p=r/rel; x=p.read_text(); p.write_text(fn(x))
edit('pubspec.yaml',lambda x:x.replace('version: 1.29.0+133','version: 1.30.0+134'))
def home(x):
 x=x.replace("_header(Icons.groups_outlined,'Персонал','Статус сотрудников')","InkWell(borderRadius:BorderRadius.circular(12),onTap:()=>context.push('/personnel'),child:_header(Icons.groups_outlined,'Персонал','Статус сотрудников'))")
 return x
edit('lib/features/home/home_screen.dart',home)
