from pathlib import Path
r=Path.cwd()

# Problems: actual UI actions must follow authoritative capabilities.
p=r/'lib/features/home/home_screen.dart';s=p.read_text()
# Resolve was made universal by an old compatibility patch. Gate the final visible action.
needle="SizedBox(width:double.infinity,child:FilledButton.icon(onPressed:()async{final id=m.id;if(id==null)return;"
if needle in s:
    s=s.replace(needle,"if(SessionService.instance.currentUser.canResolveProblems)SizedBox(width:double.infinity,child:FilledButton.icon(onPressed:()async{final id=m.id;if(id==null)return;",1)
# Dispatcher application action uses capability, not role/id heuristics.
s=s.replace("if(dispatcher&&m.id!=null&&!filed)SizedBox","if(SessionService.instance.currentUser.canFileProblemApplication&&m.id!=null&&!filed)SizedBox")
p.write_text(s)

# Annulus correction follows the same canCorrect matrix as ordinary measurement history.
p=r/'lib/features/history/history_screen.dart';s=p.read_text()
import re
s=re.sub(r"bool get _canEditAnnulus\{[^}]+\}", "bool get _canEditAnnulus=>SessionService.instance.currentUser.canCorrect;", s, count=1)
p.write_text(s)

home=(r/'lib/features/home/home_screen.dart').read_text()
hist=(r/'lib/features/history/history_screen.dart').read_text()
user=(r/'lib/core/models/user.dart').read_text()
assert "if(SessionService.instance.currentUser.canResolveProblems)SizedBox" in home
assert "if(SessionService.instance.currentUser.canFileProblemApplication&&m.id!=null&&!filed)SizedBox" in home
assert "bool get _canEditAnnulus=>SessionService.instance.currentUser.canCorrect;" in hist
assert "canCorrect => role == UserRole.shopChief || (isItr && itrSubrole != ItrSubrole.master)" in user
assert "canResolveProblems => role == UserRole.dispatcher || isItr || role == UserRole.shopChief" in user
print("v1.54g problem and annulus actions follow authoritative matrix")
