import 'dart:async';
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../../core/services/work_schedule_store.dart';
import '../../core/services/training_store.dart';
import '../../core/services/sync_service.dart';

String _dayLabel(DateTime d)=>DateFormat('dd.MM.yyyy','ru').format(d);
String _monthLabel(DateTime d)=>DateFormat('LLLL yyyy','ru').format(d);
DateTime _onlyDate(DateTime d)=>DateTime(d.year,d.month,d.day);

class WorkScheduleScreen extends StatefulWidget {
 const WorkScheduleScreen({super.key,required this.userId});
 final String userId;
 @override State<WorkScheduleScreen> createState()=>_WorkScheduleScreenState();
}
class _WorkScheduleScreenState extends State<WorkScheduleScreen>{
 DateTime shown=DateTime(DateTime.now().year,DateTime.now().month);
 DateTime? selected;
 bool editing=false;
 String paint='work';
 bool busy=false;

 @override void initState(){
   super.initState();
   unawaited(WorkScheduleStore.instance.ensureLoaded());
   unawaited(TrainingStore.instance.load());
 }
 void _moveMonth(int direction){
   setState((){
     shown=DateTime(shown.year,shown.month+direction);
     selected=null;
   });
 }
 Future<void> _tapDay(DateTime d)async{
   if(editing){
     if(busy||d.year!=shown.year||d.month!=shown.month)return;
     setState(()=>busy=true);
     try{
       await WorkScheduleStore.instance.setDayStatus(widget.userId,d,paint);
       SyncService.instance.markStateDirty();
       if(mounted)setState(()=>selected=d);
     }catch(e){
       if(mounted)ScaffoldMessenger.of(context).showSnackBar(
         SnackBar(content:Text('Не удалось изменить день: $e')));
     }finally{
       if(mounted)setState(()=>busy=false);
     }
   }else{
     setState(()=>selected=d);
   }
 }
 Widget _legend(Color color,String title)=>Padding(
   padding:const EdgeInsets.only(right:12,bottom:7),
   child:Row(mainAxisSize:MainAxisSize.min,children:[
     Container(width:12,height:12,decoration:BoxDecoration(
       color:color,borderRadius:BorderRadius.circular(4))),
     const SizedBox(width:6),Text(title),
   ]),
 );
 Color _color(String status)=>switch(status){
   'work'=>Colors.green.shade200,
   'rest'=>Colors.blue.shade100,
   'leave'=>Colors.orange.shade200,
   _=>Theme.of(context).colorScheme.surfaceContainerHighest,
 };
 Widget _calendar(){
   final first=DateTime(shown.year,shown.month);
   final offset=first.weekday-1;
   final days=DateTime(shown.year,shown.month+1,0).day;
   final cells=((days+offset+6)~/7)*7;
   final today=_onlyDate(DateTime.now());
   return Card(child:Padding(padding:const EdgeInsets.all(12),child:Column(
     children:[
       Row(children:[
         IconButton(icon:const Icon(Icons.chevron_left),
           tooltip:'Предыдущий месяц',onPressed:()=>_moveMonth(-1)),
         Expanded(child:Text(_monthLabel(shown),
           textAlign:TextAlign.center,
           style:const TextStyle(fontWeight:FontWeight.w700,fontSize:18))),
         IconButton(icon:const Icon(Icons.chevron_right),
           tooltip:'Следующий месяц',onPressed:()=>_moveMonth(1)),
       ]),
       GridView.builder(
         padding:EdgeInsets.zero,
         shrinkWrap:true,
         physics:const NeverScrollableScrollPhysics(),
         gridDelegate:const SliverGridDelegateWithFixedCrossAxisCount(
           crossAxisCount:7,mainAxisSpacing:5,crossAxisSpacing:5,childAspectRatio:1),
         itemCount:7+cells,
         itemBuilder:(context,index){
           if(index<7)return Center(child:Text(
             const ['Пн','Вт','Ср','Чт','Пт','Сб','Вс'][index],
             style:const TextStyle(fontWeight:FontWeight.w700,fontSize:12)));
           final number=index-7-offset+1;
           if(number<1||number>days)return const SizedBox.shrink();
           final day=DateTime(shown.year,shown.month,number);
           final status=WorkScheduleStore.instance.status(widget.userId,day);
           final events=TrainingStore.instance.onDay(widget.userId,day);
           final chosen=selected==day;
           final isToday=day==today;
           return Material(
             color:_color(status),
             shape:RoundedRectangleBorder(
               borderRadius:BorderRadius.circular(9),
               side:BorderSide(
                 color:chosen?Theme.of(context).colorScheme.primary:
                   isToday?Theme.of(context).colorScheme.outline:
                     Colors.transparent,
                 width:chosen?2.5:1.3,
               ),
             ),
             clipBehavior:Clip.antiAlias,
             child:InkWell(
               onTap:()=>_tapDay(day),
               child:Column(mainAxisAlignment:MainAxisAlignment.center,children:[
                 Text('$number',style:const TextStyle(color:Colors.black87,
                   fontWeight:FontWeight.w600)),
                 if(events.isNotEmpty)
                   Container(margin:const EdgeInsets.only(top:2),
                     width:8,height:8,decoration:const BoxDecoration(
                       shape:BoxShape.circle,color:Colors.red)),
               ]),
             ),
           );
         },
       ),
       const SizedBox(height:12),
       Wrap(children:[
         _legend(Colors.green.shade200,'Вахта'),
         _legend(Colors.blue.shade100,'Отдых'),
         _legend(Colors.orange.shade200,'Отпуск'),
         _legend(Colors.red,'Обучение'),
       ]),
     ],
   )));
 }
 Widget _editTools(){
   return Card(child:Padding(padding:const EdgeInsets.all(12),child:Column(
     crossAxisAlignment:CrossAxisAlignment.start,children:[
       Text('Редактирование · ${_monthLabel(shown)}',
         style:const TextStyle(fontSize:16,fontWeight:FontWeight.w700)),
       const SizedBox(height:6),
       const Text('Выберите тип дня и отмечайте даты прямо в календаре. '
         'Изменения затрагивают только выбранные дни текущего месяца.'),
       const SizedBox(height:10),
       Wrap(spacing:7,runSpacing:3,children:[
         ChoiceChip(label:const Text('Работа'),selected:paint=='work',
           avatar:const Icon(Icons.work_outline,size:18),
           onSelected:(_)=>setState(()=>paint='work')),
         ChoiceChip(label:const Text('Отдых'),selected:paint=='rest',
           avatar:const Icon(Icons.nights_stay_outlined,size:18),
           onSelected:(_)=>setState(()=>paint='rest')),
         ChoiceChip(label:const Text('Отпуск'),selected:paint=='leave',
           avatar:const Icon(Icons.beach_access_outlined,size:18),
           onSelected:(_)=>setState(()=>paint='leave')),
         ChoiceChip(label:const Text('По графику'),selected:paint=='reset',
           avatar:const Icon(Icons.restart_alt,size:18),
           onSelected:(_)=>setState(()=>paint='reset')),
       ]),
       if(busy)const LinearProgressIndicator(),
     ],
   )));
 }
 String _statusTitle(String state)=>switch(state){
   'work'=>'Вахта','rest'=>'Отдых','leave'=>'Отпуск',_=>'График ещё не задан',
 };
 Widget _dayEvents(){
   final d=selected;
   if(d==null)return const Card(child:Padding(
     padding:EdgeInsets.all(16),
     child:Text('Нажмите на дату, чтобы посмотреть события в этот день.')));
   final events=TrainingStore.instance.onDay(widget.userId,d);
   return Card(child:Padding(padding:const EdgeInsets.all(14),
     child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[
       Text('События · ${_dayLabel(d)}',
         style:const TextStyle(fontWeight:FontWeight.w700,fontSize:16)),
       const SizedBox(height:3),
       Text(_statusTitle(WorkScheduleStore.instance.status(widget.userId,d)),
         style:TextStyle(color:Theme.of(context).colorScheme.onSurfaceVariant)),
       const SizedBox(height:8),
       if(events.isEmpty)
         const Padding(padding:EdgeInsets.symmetric(vertical:9),
           child:Text('Событий нет')),
       ...events.map((training)=>ListTile(
         dense:true,
         contentPadding:EdgeInsets.zero,
         leading:const Icon(Icons.school_outlined,color:Colors.red),
         title:Text(training.title),
         subtitle:Text(training.completed?'Обучение пройдено':'Запланировано обучение'),
       )),
     ]),
   ));
 }
 @override Widget build(BuildContext context)=>Scaffold(
   appBar:AppBar(title:const Text('График работы'),actions:[
     IconButton(
       tooltip:editing?'Завершить редактирование':'Редактировать месяц',
       icon:Icon(editing?Icons.check_circle_outline:Icons.edit_calendar_outlined),
       onPressed:()=>setState(()=>editing=!editing)),
     IconButton(
       tooltip:'Настройки графика',
       icon:const Icon(Icons.settings_outlined),
       onPressed:()=>Navigator.push(context,MaterialPageRoute(
         builder:(_)=>WorkScheduleSettingsScreen(userId:widget.userId))),
     ),
   ]),
   body:ListenableBuilder(
     listenable:Listenable.merge([WorkScheduleStore.instance,TrainingStore.instance]),
     builder:(context,_)=>ListView(
       padding:const EdgeInsets.fromLTRB(12,12,12,28),
       children:[
         if(editing)_editTools(),
         _calendar(),
         _dayEvents(),
       ],
     ),
   ),
 );
}
class WorkScheduleSettingsScreen extends StatefulWidget{
 const WorkScheduleSettingsScreen({super.key,required this.userId});
 final String userId;
 @override State<WorkScheduleSettingsScreen> createState()=>_WorkScheduleSettingsState();
}
class _WorkScheduleSettingsState extends State<WorkScheduleSettingsScreen>{
 bool saving=false;
 Future<void> _change(void Function(EmployeeSchedule) change)async{
   if(saving)return;
   setState(()=>saving=true);
   try{
     await WorkScheduleStore.instance.change(widget.userId,change);
     SyncService.instance.markStateDirty();
   }catch(e){
     if(mounted)ScaffoldMessenger.of(context).showSnackBar(
       SnackBar(content:Text('Не удалось сохранить: $e')));
   }finally{
     if(mounted)setState(()=>saving=false);
   }
 }
 Future<void> _arrival()async{
   final current=WorkScheduleStore.instance.forUser(widget.userId).arrival;
   final date=await showDatePicker(
     context:context,locale:const Locale('ru','RU'),
     initialDate:current??DateTime.now(),
     firstDate:DateTime(2020),lastDate:DateTime(2100),
     helpText:'Дата заезда на вахту');
   if(date!=null)await _change((s)=>s.arrival=_onlyDate(date));
 }
 Future<void> _addVacation()async{
   final now=DateTime.now();
   final range=await showDateRangePicker(
     context:context,locale:const Locale('ru','RU'),
     firstDate:DateTime(2020),lastDate:DateTime(2100),
     initialDateRange:DateTimeRange(start:_onlyDate(now),end:_onlyDate(now)),
     helpText:'Укажите даты отпуска');
   if(range==null)return;
   await _change((s)=>s.leave.add(SchedulePeriod(
     start:_onlyDate(range.start),end:_onlyDate(range.end),type:'leave')));
 }
 Future<void> _removeVacation(SchedulePeriod p)async{
   final confirm=await showDialog<bool>(context:context,builder:(dialog)=>AlertDialog(
     title:const Text('Удалить отпуск?'),
     content:Text('${_dayLabel(p.start)} — ${_dayLabel(p.end)}'),
     actions:[
       TextButton(onPressed:()=>Navigator.pop(dialog,false),
         child:const Text('Отмена')),
       FilledButton(onPressed:()=>Navigator.pop(dialog,true),
         child:const Text('Удалить')),
     ],
   ));
   if(confirm==true)await _change((s)=>s.leave.removeWhere((x)=>
     x.start==p.start&&x.end==p.end));
 }
 @override Widget build(BuildContext context)=>Scaffold(
   appBar:AppBar(title:const Text('Настройки графика')),
   body:ListenableBuilder(listenable:WorkScheduleStore.instance,
     builder:(context,_){
       final data=WorkScheduleStore.instance.forUser(widget.userId);
       final vacations=data.leave.toList()..sort((a,b)=>a.start.compareTo(b.start));
       return ListView(padding:const EdgeInsets.all(16),children:[
         Card(child:ListTile(
           leading:const Icon(Icons.calendar_month_outlined),
           title:const Text('Дата заезда на вахту'),
           subtitle:Text(data.arrival==null?'Выберите дату':
             _dayLabel(data.arrival!)),
           trailing:const Icon(Icons.edit_outlined),
           onTap:saving?null:_arrival,
         )),
         const Padding(padding:EdgeInsets.all(12),
           child:Text('Автоматический график: месяц работы, месяц отдыха. '
             'Для нестандартного месяца используйте кнопку редактирования '
             'на основном календаре.')),
         const SizedBox(height:8),
         FilledButton.icon(
           onPressed:saving?null:_addVacation,
           icon:const Icon(Icons.beach_access_outlined),
           label:const Text('Добавить отпуск'),
         ),
         const SizedBox(height:12),
         const Text('Периоды отпуска',style:TextStyle(
           fontSize:17,fontWeight:FontWeight.w700)),
         if(vacations.isEmpty)const ListTile(title:Text('Отпуск не добавлен')),
         ...vacations.map((p)=>Card(child:ListTile(
           title:Text('${_dayLabel(p.start)} — ${_dayLabel(p.end)}'),
           trailing:IconButton(
             tooltip:'Удалить отпуск',icon:const Icon(Icons.delete_outline),
             onPressed:saving?null:()=>_removeVacation(p),
           ),
         ))),
       ]);
     }),
 );
}
