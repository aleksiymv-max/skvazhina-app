from pathlib import Path
p=Path.cwd()/'lib/features/home/home_screen.dart'
x=p.read_text()
# v1.39 compiled reliably. Keep its ListTile structure, but make dispatcher detection correct
# for both legacy dispatcher role and current ITR dispatcher subrole.
old="SessionService.instance.currentUser.role==UserRole.dispatcher&&m.id!=null"
new="(SessionService.instance.currentUser.role==UserRole.dispatcher||SessionService.instance.currentUser.itrSubrole==ItrSubrole.dispatcher)&&m.id!=null"
x=x.replace(old,new)
# Give action column enough room without exceeding compact phone layouts.
x=x.replace("trailing: SizedBox(width:150,child:Column(","trailing: SizedBox(width:132,child:Column(")
x=x.replace("SizedBox(width:150,child:FilledButton(","SizedBox(width:132,child:FilledButton(")
x=x.replace("SizedBox(width:150,child:OutlinedButton(","SizedBox(width:132,child:OutlinedButton(")
p.write_text(x)
