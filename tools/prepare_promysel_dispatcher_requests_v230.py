#!/usr/bin/env python3
"""v2.30: restore dispatcher-only action under Resolve for BOTH problem types.

Stable server audit + per-device durable queue; no user/measurement deletes.
"""
from pathlib import Path
def one(s,a,b,name):
 n=s.count(a)
 if n!=1:raise RuntimeError('v2.30 '+name+' expected 1 anchor, got '+str(n))
 return s.replace(a,b,1)

u=Path('lib/core/models/user.dart')
x=u.read_text()
x=one(x,'bool get canFileProblemApplication => role == UserRole.dispatcher;',
'''bool get canFileProblemApplication => role == UserRole.dispatcher ||
    (role == UserRole.engineer && itrSubrole == ItrSubrole.dispatcher);''',
    'ITR dispatcher role support')
u.write_text(x)

# The legacy store keyed requests only by a device-local integer, so it lost
# cross-device identity and could leak display status between fields.
store=Path('lib/core/services/problem_application_store.dart')
store.write_text(Path(__file__).with_name('problem_application_store_v230.dart').read_text())

p=Path('lib/features/home/home_screen.dart')
s=p.read_text()
start=s.index(' Future<void> _showProblems() async {')
end=s.index('\n Widget _standaloneProblemCard(',start)
block=s[start:end]
block=one(block,
 '  problems = await repo.unresolvedProblems();',
 '''  problems = await repo.unresolvedProblems();
  await ProblemApplicationStore.instance.indexMeasurements(problems);
  unawaited(ProblemApplicationStore.instance.refresh(force:true));''',
 'load event keys and remote marks')
block=one(block,
 '  await showModalBottomSheet(',
 '''  StateSetter? modalUpdater;
  void onDispatchChanged(){
   if(mounted&&modalUpdater!=null)modalUpdater!((){});
  }
  ProblemApplicationStore.instance.addListener(onDispatchChanged);
  try{
  await showModalBottomSheet(''',
 'subscribe to dispatch ledger while modal is visible')
block=one(block,'builder: (ctx, setModal) {',
 'builder: (ctx, setModal) { modalUpdater=setModal;',
 'rebuild modal after ledger change')
last=block.rfind('\\n }')
if last<0:raise RuntimeError('Cannot close modal listener after sheet')
block=block[:last]+'''\\n  }finally{ProblemApplicationStore.instance.removeListener(onDispatchChanged);}'''+block[last:]

block=one(block,
 '''                  final dispatcher=SessionService.instance.currentUser.role==UserRole.dispatcher||SessionService.instance.currentUser.itrSubrole==ItrSubrole.dispatcher;
                  final filed=m.id!=null&&ProblemApplicationStore.instance.has(m.id!);''',
 '''                  final application=m.id==null?null:
                    ProblemApplicationStore.instance.forMeasurement(m.id!);''',
 'measurement status lookup')

legacy='''                    if(SessionService.instance.currentUser.canFileProblemApplication&&m.id!=null)SizedBox(width:double.infinity,child:OutlinedButton.icon(onPressed:filed?null:(){ProblemApplicationStore.instance.file(m.id!,SessionService.instance.currentUser.name);setModal((){});if(mounted)setState((){});ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Заявка по проблеме подана')));},icon:Icon(filed?Icons.check_circle:Icons.assignment_turned_in_outlined),label:Text(filed?'Заявка подана '+_problemDate(ProblemApplicationStore.instance.data[m.id!]!.$2):'Подать заявку'))),
'''
block=one(block,legacy,'''                    if(application!=null)Padding(
                      padding:const EdgeInsets.only(bottom:8),
                      child:Text('Заявка подана: '+_problemDate(application.filedAt)+
                        (application.pending?' · ожидает отправки':'')+
                        (application.filedByName.isEmpty?'':' · '+application.filedByName),
                        style:Theme.of(context).textTheme.bodySmall)),
''',
 'show submitted timestamp ABOVE Resolve')

resolveLine="""                    if(SessionService.instance.currentUser.canResolveProblems)SizedBox(width:double.infinity,child:FilledButton.icon(onPressed:()async{final yes=await showDialog<bool>(context:context,builder:(d)=>AlertDialog(title:const Text('Подтвердить решение'),content:const Text('Отметить проблему как решённую?'),actions:[TextButton(onPressed:()=>Navigator.pop(d,false),child:const Text('Отмена')),FilledButton(onPressed:()=>Navigator.pop(d,true),child:const Text('Проблема решена'))]));if(yes!=true)return;final id=m.id;if(id==null)return;setModal(()=>problems.removeWhere((p)=>p.id==id));if(mounted)setState((){});try{if(!SessionService.instance.currentUser.canResolveProblems)throw Exception('Недостаточно прав');await repo.resolveProblem(id,SessionService.instance.currentUser.id,SessionService.instance.currentUser.name);}catch(_){if(mounted)ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Не удалось сохранить решение.')));}},icon:const Icon(Icons.check),label:const Text('Решено'))),"""
button=''' 
                    if(SessionService.instance.currentUser.canFileProblemApplication&&m.id!=null)
                      Padding(padding:const EdgeInsets.only(top:8),
                        child:SizedBox(width:double.infinity,child:OutlinedButton.icon(
                          onPressed:application!=null?null:()async{
                            try{
                              await ProblemApplicationStore.instance.file(
                                m.id!,SessionService.instance.currentUser.name);
                              if(ctx.mounted)setModal((){});
                            }catch(_){
                              if(ctx.mounted)ScaffoldMessenger.of(ctx).showSnackBar(
                                const SnackBar(content:Text('Не удалось сохранить заявку. Проверьте связь или права.')));
                            }
                          },
                          icon:const Icon(Icons.assignment_turned_in_outlined),
                          label:const Text('Подать заявку')))),
'''
block=one(block,resolveLine,resolveLine+button,
 'dispatcher button BELOW Resolve')
s=s[:start]+block+s[end:]

# A separate production report (filed from Walk) also has Resolve; ensure the
# same dispatcher flow is available there, not only for legacy walk problems.
start=s.index(' Widget _standaloneProblemCard(')
method=s[start:]
needle='''      if(SessionService.instance.currentUser.canResolveProblems)...[
        const SizedBox(height:12),'''
stamp='''      if(ProblemApplicationStore.instance.forReport(report.id)!=null)
        Padding(padding:const EdgeInsets.only(top:10,bottom:5),
          child:Text(
            'Заявка подана: '+
            _problemDate(ProblemApplicationStore.instance.forReport(report.id)!.filedAt)+
            (ProblemApplicationStore.instance.forReport(report.id)!.pending?
              ' · ожидает отправки':''),
            style:Theme.of(context).textTheme.bodySmall)),
'''
method=one(method,needle,stamp+needle,'standalone submitted timestamp')
# Include after existing resolve action. Use the exact final tail of the existing method.
needle='''       ],
    ])));
 }'''
follow='''       ],
       if(SessionService.instance.currentUser.canFileProblemApplication)...[
        const SizedBox(height:8),
        SizedBox(width:double.infinity,child:OutlinedButton.icon(
          onPressed:report.pending||
            ProblemApplicationStore.instance.hasReport(report.id)?null:()async{
            try{
              await ProblemApplicationStore.instance.fileReport(report.id);
            }catch(_){
              if(context.mounted)ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content:Text('Не удалось сохранить заявку диспетчера')));
            }
          },
          icon:const Icon(Icons.assignment_turned_in_outlined),
          label:const Text('Подать заявку'))),
       ],
    ])));
 }'''
method=one(method,needle,follow,'standalone dispatcher button below Resolve')
s=s[:start]+method
p.write_text(s)
print('PASS v2.30: dispatcher ITR role, durable per-field mark, status before Resolve, action after Resolve on legacy and standalone')
