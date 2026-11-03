import 'dart:async';
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../../core/services/training_store.dart';
import '../../core/services/sync_service.dart';

class TrainingScreen extends StatefulWidget{
 const TrainingScreen({super.key,required this.userId});
 final String userId;
 @override State<TrainingScreen> createState()=>_TrainingScreenState();
}
class _TrainingScreenState extends State<TrainingScreen>{
 bool busy=false;
 @override void initState(){
   super.initState();
   unawaited(TrainingStore.instance.load());
 }
 String _date(DateTime d)=>DateFormat('dd.MM.yyyy','ru').format(d);
 String _cadence(int months)=>switch(months){
   6=>'Раз в полгода',12=>'Раз в год',_=>'Без периодичности',
 };
 Future<void> _save(TrainingItem item,{bool update=false})async{
   if(busy)return;
   setState(()=>busy=true);
   try{
     if(update){await TrainingStore.instance.update(item);}
     else{await TrainingStore.instance.add(item);}
     SyncService.instance.markStateDirty();
   }catch(e){
     if(mounted)ScaffoldMessenger.of(context).showSnackBar(
       SnackBar(content:Text('Не удалось сохранить обучение: $e')));
   }finally{if(mounted)setState(()=>busy=false);}
 }
 Future<void> _edit({TrainingItem? item})async{
   final title=TextEditingController(text:item?.title??'');
   DateTime? selected=item?.date;
   int repeat=item?.repeatMonths??12;
   try{
     final result=await showDialog<(String,DateTime,int)>(
       context:context,
       builder:(dialog)=>StatefulBuilder(builder:(dialog,change)=>AlertDialog(
         title:Text(item==null?'Добавить обучение':'Редактировать обучение'),
         content:SingleChildScrollView(child:Column(mainAxisSize:MainAxisSize.min,children:[
           TextField(controller:title,textCapitalization:TextCapitalization.sentences,
             maxLength:160,decoration:const InputDecoration(labelText:'Название обучения')),
           DropdownButtonFormField<int>(value:repeat,isExpanded:true,
             decoration:const InputDecoration(labelText:'Периодичность'),
             items:const [
               DropdownMenuItem(value:12,child:Text('Раз в год')),
               DropdownMenuItem(value:6,child:Text('Раз в полгода')),
               DropdownMenuItem(value:0,child:Text('Без периодичности')),
             ],
             onChanged:(value){if(value!=null)change(()=>repeat=value);},
           ),
           const SizedBox(height:8),
           ListTile(contentPadding:EdgeInsets.zero,leading:const Icon(Icons.event),
             title:const Text('Дата обучения'),
             subtitle:Text(selected==null?'Выберите дату':_date(selected!)),
             onTap:()async{
               final picked=await showDatePicker(context:dialog,
                 locale:const Locale('ru','RU'),
                 initialDate:selected??DateTime.now(),
                 firstDate:DateTime(2020),lastDate:DateTime(2100),
                 helpText:'Дата обучения');
               if(picked!=null)change(()=>selected=picked);
             }),
         ])),
         actions:[
           TextButton(onPressed:()=>Navigator.pop(dialog),child:const Text('Отмена')),
           FilledButton(onPressed:(){
             final name=title.text.trim();
             if(name.isEmpty||selected==null){
               ScaffoldMessenger.of(dialog).showSnackBar(const SnackBar(
                 content:Text('Укажите название и дату обучения')));
               return;
             }
             Navigator.pop(dialog,(name,selected!,repeat));
           },child:const Text('Сохранить')),
         ],
       )),
     );
     if(result==null)return;
     final now=DateTime.now().toUtc();
     final row=TrainingItem(
       id:item?.id??'training_${now.microsecondsSinceEpoch}_${widget.userId}',
       userId:widget.userId,title:result.$1,date:result.$2,
       repeatMonths:result.$3,completedAt:item?.completedAt,
       updatedAt:now,
     );
     await _save(row,update:item!=null);
   }finally{title.dispose();}
 }
 Future<void> _complete(TrainingItem item)async{
   if(busy||item.completed)return;
   // Open the next training directly. Only ask for the date; name and
   // periodicity are inherited from the completed training.
   final today=DateTime.now();
   final proposed=TrainingStore.nextDate(today,item.repeatMonths==0?12:item.repeatMonths);
   final picked=await showDatePicker(
     context:context,locale:const Locale('ru','RU'),
     initialDate:proposed,
     firstDate:DateTime(today.year,today.month,today.day),
     lastDate:DateTime(2100),
     helpText:'Следующее обучение: ${item.title}',
     confirmText:'Назначить',
   );
   if(picked==null)return; // Do not mark completed if next date was cancelled.
   if(!mounted)return;
   setState(()=>busy=true);
   try{
     await TrainingStore.instance.completeAndReschedule(item,picked);
     SyncService.instance.markStateDirty();
     if(mounted)ScaffoldMessenger.of(context).showSnackBar(
       SnackBar(content:Text('Обучение пройдено. Следующее: ${_date(picked)}')));
   }catch(e){
     if(mounted)ScaffoldMessenger.of(context).showSnackBar(
       SnackBar(content:Text('Не удалось отметить прохождение: $e')));
   }finally{if(mounted)setState(()=>busy=false);}
 }
 Future<void> _delete(TrainingItem item)async{
   if(busy)return;
   final accepted=await showDialog<bool>(context:context,builder:(dialog)=>AlertDialog(
     title:const Text('Удалить обучение?'),
     content:Text('Удалить «${item.title}» из списка?'),
     actions:[
       TextButton(onPressed:()=>Navigator.pop(dialog,false),
         child:const Text('Отмена')),
       FilledButton(onPressed:()=>Navigator.pop(dialog,true),
         child:const Text('Удалить')),
     ],
   ));
   if(accepted!=true||!mounted)return;
   setState(()=>busy=true);
   try{
     await TrainingStore.instance.remove(item.id);
     SyncService.instance.markStateDirty();
   }catch(e){
     if(mounted)ScaffoldMessenger.of(context).showSnackBar(
       SnackBar(content:Text('Ошибка удаления: $e')));
   }finally{if(mounted)setState(()=>busy=false);}
 }
 Widget _itemCard(TrainingItem item){
   final done=item.completed;
   return Card(child:ListTile(
     leading:Icon(done?Icons.check_circle_outline:Icons.school_outlined,
       color:done?Colors.green:null),
     title:Text(item.title,style:const TextStyle(fontWeight:FontWeight.w700)),
     subtitle:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[
       Text('${done?'Пройдено':'Запланировано'}: ${_date(item.date)}'),
       Text(_cadence(item.repeatMonths)),
     ]),
     isThreeLine:true,
     trailing:PopupMenuButton<String>(
       tooltip:'Действия с обучением',
       enabled:!busy,
       icon:const Icon(Icons.more_vert),
       onSelected:(choice){
         if(choice=='complete')_complete(item);
         if(choice=='edit')_edit(item:item);
         if(choice=='delete')_delete(item);
       },
       itemBuilder:(_)=>[
         if(!done)const PopupMenuItem(value:'complete',
           child:ListTile(leading:Icon(Icons.check_circle_outline),
             title:Text('Прошёл обучение'),dense:true,
             contentPadding:EdgeInsets.zero)),
         const PopupMenuItem(value:'edit',
           child:ListTile(leading:Icon(Icons.edit_outlined),
             title:Text('Редактировать обучение'),dense:true,
             contentPadding:EdgeInsets.zero)),
         const PopupMenuItem(value:'delete',
           child:ListTile(leading:Icon(Icons.delete_outline),
             title:Text('Удалить'),dense:true,
             contentPadding:EdgeInsets.zero)),
       ],
     ),
   ));
 }
 @override Widget build(BuildContext context)=>Scaffold(
   appBar:AppBar(title:const Text('Обучение')),
   floatingActionButton:FloatingActionButton.extended(
     onPressed:busy?null:()=>_edit(),icon:const Icon(Icons.add),
     label:const Text('Добавить')),
   body:ListenableBuilder(listenable:TrainingStore.instance,builder:(context,_){
     final all=TrainingStore.instance.forUser(widget.userId);
     if(all.isEmpty)return const Center(child:Text('Обучение пока не добавлено.'));
     return ListView.builder(padding:const EdgeInsets.fromLTRB(12,12,12,90),
       itemCount:all.length,itemBuilder:(ctx,i)=>_itemCard(all[i]));
   }),
 );
}
