from pathlib import Path
p=Path('lib/features/home/home_screen.dart')
s=p.read_text()
imp="import '../admin/chief_approvals_screen.dart';"
if imp not in s:s=imp+'\n'+s

def swap(src,a,b,text):
    i=src.index(a)
    j=src.index(b,i)
    return src[:i]+text+'\n'+src[j:]

s=swap(s,' Widget _fieldDashboard()=>',' Widget _problemsDashboard()',"""
 Widget _fieldDashboard()=>Card(child:InkWell(
   onTap:()=>context.push('/wells?from=home'),
   child:Padding(padding:const EdgeInsets.all(16),
     child:_header(Icons.location_on_outlined,
       SessionService.instance.currentUser.role==UserRole.admin?'Все месторождения':
       SessionService.instance.fieldName(SessionService.instance.currentFieldId??''),
       'Участков: ${visibleAreas.length}'
     ),
   ),
 ));
""")
s=swap(s,' Widget _approvalDashboard()',' Widget _fieldDashboard()',"""
 Widget _approvalDashboard(){
   final s=SessionService.instance;
   final pending=s.allPending.where((p)=>p.fieldId==s.currentFieldId).toList();
   return Card(child:InkWell(
     onTap:()=>Navigator.of(context).push(MaterialPageRoute<void>(
       builder:(_)=>const ChiefApprovalsScreen())),
     child:Padding(padding:const EdgeInsets.all(16),
       child:_header(Icons.how_to_reg_outlined,'Заявки на согласование',
         'Ожидают решения: ${pending.length}')),
   ));
 }
""")
s=swap(s,' Widget _problemsDashboard()',' Widget _personnelDashboard()',"""
 Widget _problemsDashboard()=>Card(child:InkWell(
   onTap:_showProblems,
   child:Padding(padding:const EdgeInsets.all(16),
     child:_header(Icons.warning_amber_rounded,'Проблемы',
       'Открытых вопросов: ${problems.length}')),
 ));
""")
p.write_text(s)
print('PASS compact home and approvals')
