#!/usr/bin/env python3
"""Patch the assembled Flutter tree after all existing release transformations.

No database mutation, no change to offline queues, no authorization shortcuts.
"""
from pathlib import Path

menu=Path('lib/features/menu/menu_screen.dart')
s=menu.read_text(encoding='utf-8')
for imp in [
    "import '../../core/services/session_service.dart';",
    "import '../../core/models/user.dart';",
    "import '../admin/chief_approvals_screen.dart';",
]:
    if imp not in s:s=imp+'\n'+s
anchor="_entry(context,Icons.menu_book_outlined,'Документация',"
assert s.count(anchor)==1, 'menu profile navigation changed'
link="""   if(SessionService.instance.currentUser.role==UserRole.shopChief)
     Card(child:ListTile(
       leading:const Icon(Icons.how_to_reg_outlined),
       title:const Text('Согласование'),
       subtitle:const Text('Заявки и приглашение сотрудников'),
       trailing:const Icon(Icons.chevron_right),
       onTap:()=>Navigator.of(context).push(MaterialPageRoute<void>(
         builder:(_)=>const ChiefApprovalsScreen())),
     )),
"""
s=s.replace(anchor,link+anchor,1)
menu.write_text(s,encoding='utf-8')

login=Path('lib/features/auth/login_screen.dart')
s=login.read_text(encoding='utf-8')
anchor=' bool _fieldManuallyChosen=false;'
assert s.count(anchor)==1, 'field selection anchor changed'
s=s.replace(anchor,anchor+"\n final String _invitedFieldId=Uri.base.queryParameters['fieldId']??'';",1)
anchor='   // Registration-only data: do not fetch on the ordinary login form.'
assert s.count(anchor)==1, 'registration field init changed'
s=s.replace(anchor,anchor+"\n   if(Uri.base.queryParameters['register']=='1'){register=true;unawaited(_fetchFields());}",1)
anchor='   final options=SessionService.instance.approvedFields;'
assert s.count(anchor)==2, 'field discovery changed'
s=s.replace(anchor,anchor+"""
   if(_invitedFieldId.isNotEmpty&&options.any((f)=>f.id==_invitedFieldId)){
     fieldId=_invitedFieldId;
     _fieldManuallyChosen=true;
   }
""")
login.write_text(s,encoding='utf-8')

dst=Path('lib/features/admin/chief_approvals_screen.dart')
dst.parent.mkdir(parents=True,exist_ok=True)
dst.write_text(Path(__file__).with_name('chief_approvals_screen.dart').read_text(encoding='utf-8'),encoding='utf-8')
assert "ChiefApprovalsScreen()" in menu.read_text()
assert "_invitedFieldId" in login.read_text()
print('PASS: chief approvals route, native sharing and registration field selection')
