from pathlib import Path
r=Path.cwd()
p=r/'lib/features/home/home_screen.dart'
x=p.read_text()
start=x.index("trailing: canResolve ? Column(")
end=x.index(" : null,",start)+len(" : null,")
x=x[:start]+"trailing: null,"+x[end:]
# Avoid the broken attempt to inject siblings into ListTile. Keep compact trailing actions in a width-safe column.
marker="trailing: null,"
replacement="""trailing: SizedBox(width:150,child:Column(mainAxisSize:MainAxisSize.min,children:[
                        SizedBox(width:150,child:FilledButton(onPressed:()async{
                          final id=m.id;if(id==null)return;
                          setModal(()=>problems.removeWhere((p)=>p.id==id));
                          if(mounted)setState((){});
                          try{await repo.resolveProblem(id,SessionService.instance.currentUser.id,SessionService.instance.currentUser.name);}
                          catch(_){if(mounted)ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Не удалось сохранить решение.')));}
                        },child:const Text('Решено'))),
                        if(SessionService.instance.currentUser.role==UserRole.dispatcher&&m.id!=null)...[
                          const SizedBox(height:6),
                          SizedBox(width:150,child:OutlinedButton(
                            onPressed:ProblemApplicationStore.instance.has(m.id!)?null:(){
                              ProblemApplicationStore.instance.file(m.id!,SessionService.instance.currentUser.name);
                              setModal((){});if(mounted)setState((){});
                            },
                            child:const Text('Заявка подана'),
                          )),
                        ],
                      ])),"""
x=x.replace(marker,replacement,1)
p.write_text(x)
