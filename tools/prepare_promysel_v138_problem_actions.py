from pathlib import Path
r=Path.cwd()
def edit(p,f):
 q=r/p;x=q.read_text();q.write_text(f(x))

# Make the two problem actions react immediately and prevent repeated taps while async resolve runs.
def home(x):
 old="""FilledButton(onPressed:()async{await repo.resolveProblem(m.id!,SessionService.instance.currentUser.id,SessionService.instance.currentUser.name);setModal((){});if(mounted)setState((){});},child:const Text('Решено')),"""
 new="""FilledButton(onPressed:()async{
                          final id=m.id;if(id==null)return;
                          // Remove from the active list immediately; database work follows.
                          setModal(()=>problems.removeWhere((p)=>p.id==id));
                          if(mounted)setState((){});
                          try{await repo.resolveProblem(id,SessionService.instance.currentUser.id,SessionService.instance.currentUser.name);}
                          catch(_){if(mounted){ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Не удалось сохранить. Повторите действие.')));setModal((){});setState((){});}}
                        },child:const Text('Решено')),"""
 if old not in x: raise Exception('resolve button marker not found')
 x=x.replace(old,new)
 old2="""OutlinedButton(onPressed:(){ProblemApplicationStore.instance.file(m.id!,SessionService.instance.currentUser.name);setModal((){});if(mounted)setState((){});},child:const Text('Заявка подана')),"""
 new2="""OutlinedButton(onPressed:(){
                            final id=m.id;if(id==null)return;
                            ProblemApplicationStore.instance.file(id,SessionService.instance.currentUser.name);
                            setModal((){});if(mounted)setState((){});
                          },child:const Text('Подать заявку')),"""
 if old2 not in x: raise Exception('application button marker not found')
 return x.replace(old2,new2)
edit('lib/features/home/home_screen.dart',home)
