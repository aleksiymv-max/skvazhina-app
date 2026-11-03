import 'package:flutter/material.dart';
import '../../core/services/work_schedule_store.dart';
import '../../core/services/sync_service.dart';

class WorkScheduleScreen extends StatefulWidget {
 const WorkScheduleScreen({super.key,required this.userId});
 final String userId;
 @override State<WorkScheduleScreen> createState()=>_WorkScheduleScreenState();
}
class _WorkScheduleScreenState extends State<WorkScheduleScreen>{
 late DateTime shown=DateTime(DateTime.now().year,DateTime.now().month);
 bool saving=false;
 @override void initState(){
   super.initState();
   WorkScheduleStore.instance.ensureLoaded();
 }
 Future<void> _change(void Function(EmployeeSchedule) change)async{
   if(saving)return;
   setState(()=>saving=true);
   try{
     await WorkScheduleStore.instance.change(widget.userId,change);
     SyncService.instance.markStateDirty();
   }catch(e){
     if(mounted)ScaffoldMessenger.of(context).showSnackBar(
       SnackBar(content:Text('Не удалось сохранить график: $e')));
   }finally{if(mounted)setState(()=>saving=false);}
 }
 Future<void> _arrival()async{
   final store=WorkScheduleStore.instance;
   final date=await showDatePicker(
     context:context,initialDate:store.forUser(widget.userId).arrival??DateTime.now(),
     firstDate:DateTime(2020),lastDate:DateTime(2100),
     helpText:'Укажите дату заезда на вахту');
   if(date!=null)await _change((v)=>v.arrival=date);
 }
 Future<void> _addPeriod(String type)async{
   final range=await showDateRangePicker(context:context,
     firstDate:DateTime(2020),lastDate:DateTime(2100),
     initialDateRange:null,
     helpText:type=='leave'?'Даты отпуска':type=='work'?'Даты работы':'Даты отдыха');
   if(range==null)return;
   await _change((v){
     final item=SchedulePeriod(start:DateTime(range.start.year,range.start.month,range.start.day),
       end:DateTime(range.end.year,range.end.month,range.end.day),type:type);
     if(type=='leave'){v.leave.add(item);}
     else{v.overrides.add(item);}
   });
 }
 Future<void> _removePeriod(SchedulePeriod p,bool vacation)async{
   await _change((v){
     if(vacation){v.leave.remove(p);}else{v.overrides.remove(p);}
   });
 }
 String _format(DateTime d)=>'${d.day.toString().padLeft(2,'0')}.${d.month.toString().padLeft(2,'0')}.${d.year}';
 String _month(int m)=>const ['Январь','Февраль','Март','Апрель','Май','Июнь',
   'Июль','Август','Сентябрь','Октябрь','Ноябрь','Декабрь'][m-1];
 Widget _legend(Color color,String name)=>Padding(
   padding:const EdgeInsets.only(right:12,bottom:8),
   child:Row(mainAxisSize:MainAxisSize.min,children:[
    Container(width:13,height:13,decoration:BoxDecoration(
      color:color,borderRadius:BorderRadius.circular(3))),
    const SizedBox(width:6),Text(name)]));
 Color _color(BuildContext context,String status){
   final c=Theme.of(context).colorScheme;
   return switch(status){
     'work'=>Colors.green.shade200,
     'rest'=>Colors.blue.shade100,
     'leave'=>Colors.orange.shade200,
     _=>c.surfaceContainerHighest,
   };
 }
 Widget _calendar(BuildContext context){
   final monthStart=DateTime(shown.year,shown.month,1);
   final offset=monthStart.weekday-1;
   final days=DateTime(shown.year,shown.month+1,0).day;
   final count=((days+offset+6)~/7)*7;
   final today=DateTime.now();
   return Card(child:Padding(padding:const EdgeInsets.all(12),child:Column(children:[
    Row(children:[
      IconButton(tooltip:'Предыдущий месяц',
        onPressed:()=>setState(()=>shown=DateTime(shown.year,shown.month-1)),
        icon:const Icon(Icons.chevron_left)),
      Expanded(child:Text('${_month(shown.month)} ${shown.year}',
        textAlign:TextAlign.center,style:const TextStyle(fontWeight:FontWeight.bold,fontSize:17))),
      IconButton(tooltip:'Следующий месяц',
        onPressed:()=>setState(()=>shown=DateTime(shown.year,shown.month+1)),
        icon:const Icon(Icons.chevron_right)),
    ]),
    GridView.builder(
      padding:EdgeInsets.zero,
      shrinkWrap:true,
      physics:const NeverScrollableScrollPhysics(),
      gridDelegate:const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount:7,mainAxisSpacing:5,crossAxisSpacing:5,childAspectRatio:1),
      itemCount:7+count,
      itemBuilder:(context,index){
        if(index<7)return Center(child:Text(
          const ['Пн','Вт','Ср','Чт','Пт','Сб','Вс'][index],
          style:const TextStyle(fontWeight:FontWeight.w600,fontSize:12)));
        final day=index-7-offset+1;
        if(day<1||day>days)return const SizedBox.shrink();
        final date=DateTime(shown.year,shown.month,day);
        final state=WorkScheduleStore.instance.status(widget.userId,date);
        final isToday=date.year==today.year&&date.month==today.month&&date.day==today.day;
        return DecoratedBox(decoration:BoxDecoration(
          color:_color(context,state),
          borderRadius:BorderRadius.circular(9),
          border:isToday?Border.all(color:Theme.of(context).colorScheme.primary,width:2):null),
          child:Center(child:Text('$day',style:const TextStyle(
            fontWeight:FontWeight.w600,color:Colors.black87))),
        );
      },
    ),
    const SizedBox(height:12),
    Wrap(children:[
      _legend(Colors.green.shade200,'Вахта'),
      _legend(Colors.blue.shade100,'Отдых'),
      _legend(Colors.orange.shade200,'Отпуск'),
    ]),
   ])));
 }
 Widget _periods(String title,List<SchedulePeriod> periods,bool vacation){
   return Card(child:ExpansionTile(
     title:Text(title,style:const TextStyle(fontWeight:FontWeight.w700)),
     children:periods.isEmpty
       ?[const ListTile(title:Text('Нет записей'))]
       :List.generate(periods.length,(index){
         final p=periods[index];
         return ListTile(
           title:Text('${_format(p.start)} — ${_format(p.end)}'),
           subtitle:vacation?const Text('Отпуск')
             :Text(p.type=='work'?'Вахта (корректировка)':'Отдых (корректировка)'),
           trailing:IconButton(
             tooltip:'Удалить период',icon:const Icon(Icons.delete_outline),
             onPressed:()async{
               final ok=await showDialog<bool>(context:context,builder:(ctx)=>AlertDialog(
                 title:const Text('Удалить период?'),
                 content:Text('${_format(p.start)} — ${_format(p.end)}'),
                 actions:[
                   TextButton(onPressed:()=>Navigator.pop(ctx,false),
                     child:const Text('Отмена')),
                   FilledButton(onPressed:()=>Navigator.pop(ctx,true),
                     child:const Text('Удалить')),
                 ]));
               if(ok==true)await _change((v){
                 (vacation?v.leave:v.overrides).removeWhere((x)=>
                   x.start==p.start&&x.end==p.end&&x.type==p.type);
               });
             },
           ),
         );
       }),
   ));
 }
 @override Widget build(BuildContext context)=>Scaffold(
   appBar:AppBar(title:const Text('График работы')),
   body:ListenableBuilder(listenable:WorkScheduleStore.instance,builder:(context,_){
     final record=WorkScheduleStore.instance.forUser(widget.userId);
     return ListView(padding:const EdgeInsets.all(16),children:[
       ListTile(
         leading:const Icon(Icons.calendar_today_outlined),
         title:const Text('Дата заезда на вахту'),
         subtitle:Text(record.arrival==null?'Не выбрана':_format(record.arrival!)),
         trailing:const Icon(Icons.edit_calendar_outlined),
         onTap:saving?null:_arrival,
       ),
       const Padding(padding:EdgeInsets.all(8),child:Text(
         'После заезда автоматически строится график: один календарный месяц '
         'работы, затем один месяц отдыха. Нестандартные осенние смены '
         'отметьте как корректировки, отпуск можно разделить на части.',
       )),
       _calendar(context),
       const SizedBox(height:8),
       FilledButton.icon(
         onPressed:saving?null:()=>_addPeriod('leave'),
         icon:const Icon(Icons.beach_access_outlined),
         label:const Text('Добавить отпуск'),
       ),
       const SizedBox(height:8),
       OutlinedButton.icon(
         onPressed:saving?null:()=>_addPeriod('work'),
         icon:const Icon(Icons.work_outline),
         label:const Text('Корректировка: работаю'),
       ),
       OutlinedButton.icon(
         onPressed:saving?null:()=>_addPeriod('rest'),
         icon:const Icon(Icons.nights_stay_outlined),
         label:const Text('Корректировка: отдыхаю'),
       ),
       _periods('Отпуска · ${record.leave.length}',record.leave,true),
       _periods('Корректировки · ${record.overrides.length}',record.overrides,false),
       const SizedBox(height:28),
     ]);
   }),
 );
}
