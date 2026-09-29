from pathlib import Path
r=Path.cwd()
p=r/'lib/features/home/home_screen.dart'
x=p.read_text()
start=x.index("trailing: canResolve ? Column(")
end=x.index(" : null,",start)+len(" : null,")
new="""trailing: null,"""
x=x[:start]+new+x[end:]
# Put actions below the text instead of squeezing them into ListTile.trailing.
needle="""isThreeLine: true,"""
# Only the two problem cards are built from this block; replace first matching block after problem section.
pos=x.index("subtitle: Text('${m.problemNote")
ip=x.index(needle,pos)+len(needle)
actions="""
                      titleAlignment: ListTileTitleAlignment.top,
                    ),
                    Padding(
                      padding: const EdgeInsets.fromLTRB(16,0,16,12),
                      child: Row(children:[
                        Expanded(child:FilledButton(
                          onPressed:()async{
                            final id=m.id;if(id==null)return;
                            setModal(()=>problems.removeWhere((p)=>p.id==id));
                            if(mounted)setState((){});
                            try{await repo.resolveProblem(id,SessionService.instance.currentUser.id,SessionService.instance.currentUser.name);}
                            catch(_){if(mounted){ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Не удалось сохранить решение.')));}}
                          },
                          child:const Text('Решено'),
                        )),
                        if(SessionService.instance.currentUser.role==UserRole.dispatcher&&m.id!=null)...[
                          const SizedBox(width:10),
                          Expanded(child:ProblemApplicationStore.instance.has(m.id!)
                            ? OutlinedButton(onPressed:null,child:const Text('Заявка подана'))
                            : OutlinedButton(onPressed:(){
                                final id=m.id;if(id==null)return;
                                ProblemApplicationStore.instance.file(id,SessionService.instance.currentUser.name);
                                setModal((){});if(mounted)setState((){});
                              },child:const Text('Подать заявку'))),
                        ],
                      ]),
                    ),
"""
# Existing ListTile closes shortly after isThreeLine. Replace its close and inject row.
close=x.index("),",ip)
x=x[:ip]+x[ip:close]+actions+x[close+2:]
p.write_text(x)
