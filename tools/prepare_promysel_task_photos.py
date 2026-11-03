"""Attach task photos at creation/completion; preserve existing task and role logic."""
from pathlib import Path
r=Path.cwd()
p=r/'lib/features/tasks/tasks_screen.dart'
s=p.read_text()
imports="import '../../core/services/task_photo_service.dart';\nimport 'task_photo_widgets.dart';\n"
assert "import '../../core/services/sync_service.dart';" in s
s=s.replace("import '../../core/services/sync_service.dart';","import '../../core/services/sync_service.dart';\n"+imports,1)
if "import 'dart:async';" not in s:s="import 'dart:async';\n"+s

start=s.index(" Future<void> _create()async{")
end=s.index(" List<(String,String)> _targets(",start)
method=""" Future<void> _showTaskPhotos(WorkTask task) async {
   await Navigator.push(context,MaterialPageRoute(builder:(_)=>TaskPhotoGallery(task:task)));
 }
 Future<void> _completeWithPhotos(WorkTask task) async {
   final selection=TaskPhotoSelectionController();
   bool sending=false;String? error;
   await showDialog<void>(context:context,builder:(ctx)=>StatefulBuilder(
     builder:(ctx,update)=>AlertDialog(
       title:const Text('Завершить задание'),
       content:SingleChildScrollView(child:Column(mainAxisSize:MainAxisSize.min,
         crossAxisAlignment:CrossAxisAlignment.start,children:[
           Text(task.title),const SizedBox(height:12),
           TaskPhotoPicker(photos:selection),
           if(sending)const LinearProgressIndicator(),
           if(error!=null)Padding(padding:const EdgeInsets.only(top:8),
             child:Text(error!,style:TextStyle(color:Theme.of(ctx).colorScheme.error))),
         ])),
       actions:[
         TextButton(onPressed:sending?null:()=>Navigator.pop(ctx),child:const Text('Отмена')),
         FilledButton.icon(icon:const Icon(Icons.check_circle_outline),
           onPressed:sending?null:()async{
             update((){sending=true;error=null;});
             try{
               if(selection.photos.isNotEmpty){
                 await TaskPhotoService.instance.upload(task,'completion',selection.photos);
               }
               final ok=store.complete(task,SessionService.instance.currentUser.name);
               if(!ok)throw Exception('Задание уже закрыто или изменило статус');
               if(ctx.mounted)Navigator.pop(ctx);
               if(mounted)ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
                 content:Text('Задание выполнено. Фотографии сохранены.')));
             }catch(e){if(ctx.mounted)update(()=>error=e.toString());}
             finally{if(ctx.mounted)update(()=>sending=false);}
           },label:const Text('Отметить выполненным'))
       ])));
   selection.dispose();
 }
 Future<void> _create()async{
   final title=TextEditingController(),description=TextEditingController();
   final selected=TaskPhotoSelectionController();
   final me=SessionService.instance.currentUser;
   final people=SessionService.instance.approvedWorkers.where(
     (x)=>x.role!=UserRole.admin&&x.id!=me.id).toList();
   final canAllOperators=me.role==UserRole.shopChief||
       (me.role==UserRole.engineer&&me.itrSubrole==ItrSubrole.master);
   String mode='personal',targetName='';
   String? targetId,error;
   bool sending=false;
   List<WorkTask>? drafts;
   List<(String,String)> options(String m)=>switch(m){
     'personal'=>people.map((x)=>(x.id,x.name+' · '+x.role.label)).toList(),
     'area'=>demoAreas.where((x)=>SessionService.instance.canSeeField(x.fieldId))
       .map((x)=>(x.id,x.name)).toList(),
     'pad'=>demoPads.where((x)=>SessionService.instance.canSeeField(x.fieldId))
       .map((x)=>(x.id,x.name+' · '+x.areaName)).toList(),
     _=><(String,String)>[],
   };
   void selectFirst(String m){
     final a=options(m);
     if(a.isEmpty){targetId=null;targetName='';}
     else{targetId=a.first.$1;targetName=a.first.$2;}
   }
   selectFirst(mode);
   await showDialog<void>(context:context,builder:(ctx)=>StatefulBuilder(
     builder:(ctx,update){
       Future<void> submit()async{
         if(sending)return;
         if(title.text.trim().isEmpty){update(()=>error='Введите название задания');return;}
         if(mode!='allOperators'&&targetId==null){
           update(()=>error='Выберите получателя');return;
         }
         if(drafts==null){
           final stamp=DateTime.now().microsecondsSinceEpoch.toString();
           final now=DateTime.now();
           if(mode=='allOperators'){
             final operators=SessionService.instance.approvedWorkers.where(
               (x)=>x.role==UserRole.operator).toList();
             if(operators.isEmpty){update(()=>error='Нет операторов для выдачи');return;}
             drafts=[for(var i=0;i<operators.length;i++)
               WorkTask(id:stamp+'_'+i.toString(),
                 title:title.text.trim(),description:description.text.trim(),
                 createdBy:me.name,createdById:me.id,createdAt:now,
                 targetType:WorkTaskTarget.personal,targetId:operators[i].id,
                 targetName:operators[i].name)];
           }else{
             final type=switch(mode){
               'personal'=>WorkTaskTarget.personal,
               'area'=>WorkTaskTarget.area,_=>WorkTaskTarget.pad};
             drafts=[WorkTask(id:stamp,title:title.text.trim(),
               description:description.text.trim(),createdBy:me.name,
               createdById:me.id,createdAt:now,targetType:type,
               targetId:targetId!,targetName:targetName)];
           }
         }
         update((){sending=true;error=null;});
         try{
           if(selected.photos.isNotEmpty){
             // Keep the dialog open on failure. Same task/photo ids on retry.
             for(final task in drafts!){
               await TaskPhotoService.instance.register(task);
               await TaskPhotoService.instance.upload(task,'assignment',selected.photos);
             }
           }
           for(final task in drafts!){
             store.add(task);
             if(selected.photos.isEmpty){
               unawaited(TaskPhotoService.instance.register(task).catchError((_){ }));
             }
             if(task.targetType==WorkTaskTarget.personal){
               NotificationStore.instance.add(AppNotice(
                 id:'task_'+task.id,userId:task.targetId,
                 title:'Новое задание',body:task.title,createdAt:DateTime.now()));
             }
           }
           if(ctx.mounted)Navigator.pop(ctx);
         }catch(e){if(ctx.mounted)update(()=>error='Не удалось прикрепить фото: '+e.toString());}
         finally{if(ctx.mounted)update(()=>sending=false);}
       }
       return Dialog(child:ConstrainedBox(
         constraints:const BoxConstraints(maxWidth:440,maxHeight:660),
         child:Padding(padding:const EdgeInsets.all(18),
           child:Column(mainAxisSize:MainAxisSize.min,crossAxisAlignment:CrossAxisAlignment.start,
             children:[
               const Text('Новое задание',
                 style:TextStyle(fontSize:20,fontWeight:FontWeight.w900)),
               const SizedBox(height:12),
               Flexible(child:SingleChildScrollView(child:Column(
                 crossAxisAlignment:CrossAxisAlignment.start,children:[
                   TextField(controller:title,enabled:!sending,
                     decoration:const InputDecoration(labelText:'Название')),
                   const SizedBox(height:10),
                   TextField(controller:description,maxLines:3,enabled:!sending,
                     decoration:const InputDecoration(labelText:'Описание')),
                   const SizedBox(height:10),
                   DropdownButtonFormField<String>(
                     key:ValueKey('mode-'+mode),initialValue:mode,
                     decoration:const InputDecoration(labelText:'Кому назначить'),
                     items:[
                       const DropdownMenuItem(value:'personal',child:Text('Сотруднику')),
                       if(canAllOperators)const DropdownMenuItem(
                         value:'allOperators',child:Text('Всем операторам')),
                       const DropdownMenuItem(value:'area',child:Text('Участку')),
                       const DropdownMenuItem(value:'pad',child:Text('Кусту')),
                     ],
                     onChanged:sending?null:(v){if(v==null)return;update((){
                       mode=v;drafts=null;
                       if(mode=='allOperators'){targetId=null;targetName='Все операторы';}
                       else selectFirst(mode);
                     });}),
                   const SizedBox(height:10),
                   if(mode!='allOperators')
                     if(options(mode).isEmpty)
                       const Text('Нет доступных получателей')
                     else DropdownButtonFormField<String>(
                       key:ValueKey('target-'+mode+'-'+(targetId??'')),
                       initialValue:targetId,isExpanded:true,
                       decoration:const InputDecoration(labelText:'Получатель'),
                       items:options(mode).map((x)=>DropdownMenuItem(
                         value:x.$1,child:Text(x.$2,overflow:TextOverflow.ellipsis))).toList(),
                       onChanged:sending?null:(v){
                         if(v==null)return;
                         final item=options(mode).firstWhere((x)=>x.$1==v);
                         update((){targetId=item.$1;targetName=item.$2;drafts=null;});
                       }),
                   if(mode=='allOperators')const Padding(
                     padding:EdgeInsets.symmetric(vertical:8),
                     child:Text('Задание будет выдано каждому оператору отдельно.')),
                   const SizedBox(height:16),
                   TaskPhotoPicker(photos:selected),
                   if(sending)const LinearProgressIndicator(),
                   if(error!=null)Padding(padding:const EdgeInsets.only(top:8),
                     child:Text(error!,style:TextStyle(color:Theme.of(ctx).colorScheme.error))),
                 ]))),
               const SizedBox(height:12),
               Row(mainAxisAlignment:MainAxisAlignment.end,children:[
                 TextButton(onPressed:sending?null:()=>Navigator.pop(ctx),
                   child:const Text('Отмена')),
                 const SizedBox(width:6),
                 FilledButton(onPressed:sending?null:submit,child:const Text('Выдать')),
               ]),
             ]))));
     }));
   selected.dispose();title.dispose();description.dispose();
 }

"""
s=s[:start]+method+s[end:]
old="onPressed:()=>setState(()=>store.complete(t,SessionService.instance.currentUser.name))"
assert s.count(old)==1,'completion button changed'
s=s.replace(old,"onPressed:()=>_completeWithPhotos(t)",1)
# The task's photo gallery is available to both employee and creator.
anchor="const SizedBox(height:12),if(t.status==WorkTaskStatus.active"
assert s.count(anchor)==1,'task detail anchor changed'
s=s.replace(anchor,"TextButton.icon(onPressed:()=>_showTaskPhotos(t),icon:const Icon(Icons.photo_library_outlined),label:const Text('Фотографии задания')),const SizedBox(height:12),if(t.status==WorkTaskStatus.active",1)
# Add gallery to issued tasks as well.
anchor2="if(t.status==WorkTaskStatus.awaitingConfirmation&&_canReviewTask(t,SessionService.instance.currentUser))"
assert s.count(anchor2)==1,'issued task anchor changed'
s=s.replace(anchor2,"TextButton.icon(onPressed:()=>_showTaskPhotos(t),icon:const Icon(Icons.photo_library_outlined),label:const Text('Фотографии')), "+anchor2,1)
p.write_text(s)
# Photos remain accessible after task is confirmed and moved into History.
history=r/'lib/features/history/history_screen.dart'
h=history.read_text()
assert "import '../../core/models/work_task.dart';" in h
h=h.replace("import '../../core/models/work_task.dart';","import '../../core/models/work_task.dart';\nimport '../tasks/task_photo_widgets.dart';",1)
anchor="isThreeLine:true)))]);"
assert h.count(anchor)==1,'History confirmed task card changed'
h=h.replace(anchor,"isThreeLine:true,trailing:IconButton(tooltip:'Фотографии',icon:const Icon(Icons.photo_library_outlined),onPressed:()=>Navigator.push(context,MaterialPageRoute(builder:(_)=>TaskPhotoGallery(task:t)))))))]);",1)
history.write_text(h)
print('PASS: task photos on creation, completion, issued cards and confirmed history')
