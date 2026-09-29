from pathlib import Path
p=Path.cwd()/'lib/features/home/home_screen.dart'
x=p.read_text()
anchor="subtitle: Text('${m.problemNote"
pos=x.index(anchor)
ls=x.rfind("ListTile(",0,pos)
def match(s,o):
 d=0;q=None;e=False
 for i in range(o,len(s)):
  c=s[i]
  if q:
   if e:e=False
   elif c=="\\":e=True
   elif c==q:q=None
   continue
  if c in ("'",'"'):q=c;continue
  if c=="(":d+=1
  elif c==")":
   d-=1
   if d==0:return i
 raise RuntimeError("unbalanced")
le=match(x,x.index("(",ls))+1
tile=x[ls:le]
tp=tile.index("trailing: SizedBox(width:150")
eo=tile.index("(",tp); ee=match(tile,eo)+1
cm=ee
while cm<len(tile) and tile[cm].isspace():cm+=1
if cm<len(tile) and tile[cm]==",":cm+=1
tile=tile[:tp]+"trailing:null,"+tile[cm:]
actions=r"""Padding(padding:const EdgeInsets.fromLTRB(16,0,16,14),child:Column(crossAxisAlignment:CrossAxisAlignment.stretch,children:[
FilledButton(onPressed:()async{final id=m.id;if(id==null)return;setModal(()=>problems.removeWhere((p)=>p.id==id));if(mounted)setState((){});try{await repo.resolveProblem(id,SessionService.instance.currentUser.id,SessionService.instance.currentUser.name);}catch(_){if(mounted)ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Не удалось сохранить решение.')));}},child:const Text('Решено')),
if((SessionService.instance.currentUser.role==UserRole.dispatcher||SessionService.instance.currentUser.itrSubrole==ItrSubrole.dispatcher)&&m.id!=null)...[
const SizedBox(height:8),
OutlinedButton.icon(onPressed:ProblemApplicationStore.instance.has(m.id!)?null:(){ProblemApplicationStore.instance.file(m.id!,SessionService.instance.currentUser.name);setModal((){});if(mounted)setState((){});},icon:Icon(ProblemApplicationStore.instance.has(m.id!)?Icons.check_circle_outline:Icons.assignment_turned_in_outlined),label:const Text('Заявка подана')),
if(ProblemApplicationStore.instance.has(m.id!)) Padding(padding:const EdgeInsets.only(top:6),child:Text('${ProblemApplicationStore.instance.get(m.id!)!.$1} · ${_problemDate(ProblemApplicationStore.instance.get(m.id!)!.$2)}',textAlign:TextAlign.center,style:Theme.of(context).textTheme.bodySmall)),
]])"""
x=x[:ls]+"Column(crossAxisAlignment:CrossAxisAlignment.stretch,children:["+tile+","+actions+"])"+x[le:]
p.write_text(x)
