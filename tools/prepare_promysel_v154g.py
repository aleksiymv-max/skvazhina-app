from pathlib import Path
r=Path.cwd()

# Problems: actual UI actions must follow authoritative capabilities.
p=r/'lib/features/home/home_screen.dart';s=p.read_text()
# Resolve was made universal by an old compatibility patch. Gate the final visible action.
needle="SizedBox(width:double.infinity,child:FilledButton.icon(onPressed:()async{"
if needle in s and "canResolveProblems)SizedBox(width:double.infinity,child:FilledButton.icon" not in s:
    # The final generated card may contain confirmation code before id=m.id.
    pos=s.find(needle)
    tail=s[pos:pos+1400]
    if "Решено" not in tail and "Проблема решена" not in tail: raise SystemExit("resolve action not found near FilledButton")
    s=s[:pos]+"if(SessionService.instance.currentUser.canResolveProblems)"+s[pos:]
# Dispatcher application action uses capability, not role/id heuristics.
for old in [
    "if(dispatcher&&m.id!=null&&!filed)SizedBox",
    "if(dispatcher&&m.id!=null)SizedBox",
    "if(m.id!=null&&(SessionService.instance.currentUser.role==UserRole.dispatcher||SessionService.instance.currentUser.itrSubrole==ItrSubrole.dispatcher||SessionService.instance.currentUser.id.startsWith('disp-')))...["
]:
    if old in s:
        if old.endswith("...["):
            s=s.replace(old,"if(m.id!=null&&SessionService.instance.currentUser.canFileProblemApplication)...[",1)
        else:
            s=s.replace(old,old.replace("dispatcher","SessionService.instance.currentUser.canFileProblemApplication"),1)
        break
# Final fallback: locate the action by its visible label and gate its enclosing SizedBox.
if "canFileProblemApplication" not in s:
    label=s.find("Подать заявку")
    if label<0: raise SystemExit("problem application action missing")
    box=s.rfind("SizedBox(width:double.infinity",0,label)
    if box<0: raise SystemExit("problem application button container missing")
    s=s[:box]+"if(SessionService.instance.currentUser.canFileProblemApplication)"+s[box:]
p.write_text(s)

# Annulus correction follows the same canCorrect matrix as ordinary measurement history.
p=r/'lib/features/history/history_screen.dart';s=p.read_text()
import re
s=re.sub(r"bool get _canEditAnnulus\{[^}]+\}", "bool get _canEditAnnulus=>SessionService.instance.currentUser.canCorrect;", s, count=1)
p.write_text(s)

home=(r/'lib/features/home/home_screen.dart').read_text()
hist=(r/'lib/features/history/history_screen.dart').read_text()
user=(r/'lib/core/models/user.dart').read_text()
assert "canResolveProblems)SizedBox(width:double.infinity,child:FilledButton.icon" in home
assert "canFileProblemApplication" in home and "Подать заявку" in home
assert "bool get _canEditAnnulus=>SessionService.instance.currentUser.canCorrect;" in hist
assert "canCorrect => role == UserRole.shopChief || (isItr && itrSubrole != ItrSubrole.master)" in user
assert "canResolveProblems => role == UserRole.dispatcher || isItr || role == UserRole.shopChief" in user
print("v1.54g problem and annulus actions follow authoritative matrix")
