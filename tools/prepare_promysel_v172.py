from pathlib import Path
import re
r=Path.cwd()
p=r/'lib/features/tasks/tasks_screen.dart';s=p.read_text()
start=s.index(' Future<void> _create()async{')
end=s.index('\n List<(String,String)> _targets',start)
method=r''' Future<void> _create()async{
  final title=TextEditingController(),desc=TextEditingController();
  final me=SessionService.instance.currentUser;
  final people=SessionService.instance.approvedWorkers.where((x)=>x.role!=UserRole.admin&&x.id!=me.id).toList();
  final canAllOperators=me.role==UserRole.shopChief||(me.role==UserRole.engineer&&me.itrSubrole==ItrSubrole.master);
  String mode='personal';String? targetId;String targetName='';
  List<(String,String)> options(String m)=>switch(m){
    'personal'=>people.map((u)=>(u.id,'${u.name} · ${u.role.label}')).toList(),
    'area'=>demoAreas.where((a)=>SessionService.instance.canSeeField(a.fieldId)).map((a)=>(a.id,a.name)).toList(),
    'pad'=>demoPads.where((p)=>SessionService.instance.canSeeField(p.fieldId)).map((p)=>(p.id,'${p.name} · ${p.areaName}')).toList(),
    _=><(String,String)>[]};
  void selectFirst(String m){final xs=options(m);if(xs.isEmpty){targetId=null;targetName='';}else{targetId=xs.first.$1;targetName=xs.first.$2;}}
  selectFirst(mode);
  await showDialog(context:context,builder:(c)=>StatefulBuilder(builder:(c,setD)=>Dialog(child:ConstrainedBox(constraints:const BoxConstraints(maxWidth:430,maxHeight:620),child:Padding(padding:const EdgeInsets.all(18),child:Column(mainAxisSize:MainAxisSize.min,crossAxisAlignment:CrossAxisAlignment.start,children:[
    const Text('Новое задание',style:TextStyle(fontSize:21,fontWeight:FontWeight.w900)),const SizedBox(height:14),
    Flexible(child:SingleChildScrollView(child:Column(children:[
      TextField(controller:title,decoration:const InputDecoration(labelText:'Название')),const SizedBox(height:10),
      TextField(controller:desc,maxLines:3,decoration:const InputDecoration(labelText:'Описание')),const SizedBox(height:10),
      DropdownButtonFormField<String>(key:ValueKey('mode-$mode'),initialValue:mode,decoration:const InputDecoration(labelText:'Кому назначить'),isExpanded:true,items:[
        const DropdownMenuItem(value:'personal',child:Text('Конкретному сотруднику')),
        if(canAllOperators)const DropdownMenuItem(value:'allOperators',child:Text('Всем операторам')),
        const DropdownMenuItem(value:'area',child:Text('Участку')),
        const DropdownMenuItem(value:'pad',child:Text('Кустовой площадке')),
      ],onChanged:(v){if(v==null)return;setD((){mode=v;if(mode=='allOperators'){targetId=null;targetName='Все операторы';}else{selectFirst(mode);}});}),
      const SizedBox(height:10),
      if(mode=='allOperators')Container(width:double.infinity,padding:const EdgeInsets.all(12),decoration:BoxDecoration(border:Border.all(color:Theme.of(c).colorScheme.outlineVariant),borderRadius:BorderRadius.circular(12)),child:Text('Задание будет выдано отдельно каждому оператору. Каждый оператор выполнит и закроет свою копию задания.',style:Theme.of(c).textTheme.bodyMedium))
      else if(options(mode).isEmpty)const Align(alignment:Alignment.centerLeft,child:Text('Нет доступных получателей.'))
      else DropdownButtonFormField<String>(key:ValueKey('target-$mode-$targetId'),initialValue:targetId,decoration:InputDecoration(labelText:switch(mode){'personal'=>'Выберите сотрудника','area'=>'Выберите участок',_=>'Выберите куст'}),isExpanded:true,items:options(mode).map((x)=>DropdownMenuItem(value:x.$1,child:Text(x.$2,overflow:TextOverflow.ellipsis))).toList(),onChanged:(v){if(v==null)return;final x=options(mode).firstWhere((x)=>x.$1==v);setD((){targetId=x.$1;targetName=x.$2;});}),
    ]))),const SizedBox(height:14),
    Row(mainAxisAlignment:MainAxisAlignment.end,children:[TextButton(onPressed:()=>Navigator.pop(c),child:const Text('Отмена')),const SizedBox(width:8),FilledButton(onPressed:(){
      if(title.text.trim().isEmpty)return;
      if(mode=='allOperators'){
        final ops=SessionService.instance.approvedWorkers.where((x)=>x.role==UserRole.operator).toList();if(ops.isEmpty){ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Нет операторов для назначения.')));return;}
        final batch=DateTime.now().microsecondsSinceEpoch;for(var i=0;i<ops.length;i++){final op=ops[i];store.add(WorkTask(id:'${batch}_$i',title:title.text.trim(),description:desc.text.trim(),createdBy:me.name,createdById:me.id,createdAt:DateTime.now(),targetType:WorkTaskTarget.personal,targetId:op.id,targetName:op.name));}
      }else{
        if(targetId==null)return;final type=switch(mode){'personal'=>WorkTaskTarget.personal,'area'=>WorkTaskTarget.area,_=>WorkTaskTarget.pad};
        store.add(WorkTask(id:DateTime.now().microsecondsSinceEpoch.toString(),title:title.text.trim(),description:desc.text.trim(),createdBy:me.name,createdById:me.id,createdAt:DateTime.now(),targetType:type,targetId:targetId!,targetName:targetName));
      }
      Navigator.pop(c);
    },child:const Text('Выдать'))
    ])
  ]))))));
  title.dispose();desc.dispose();if(mounted)setState((){});
 }
'''
s=s[:start]+method+s[end:]
p.write_text(s)

# Version and deterministic gates.
p=r/'pubspec.yaml';v=p.read_text();v=re.sub(r'version:\s*[^\n]+','version: 1.72.0+176',v,count=1);p.write_text(v)
t=(r/'lib/features/tasks/tasks_screen.dart').read_text()
assert "value:'allOperators',child:Text('Всем операторам')" in t
assert "key:ValueKey('target-$mode-$targetId')" in t
assert "'personal'=>people.map" in t
assert "ops=SessionService.instance.approvedWorkers.where((x)=>x.role==UserRole.operator)" in t
assert "targetType:WorkTaskTarget.personal,targetId:op.id,targetName:op.name" in t
print('v1.72 task assignment flow gates passed')
