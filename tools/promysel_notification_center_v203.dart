import 'dart:async';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../core/services/promysel_notification_hub.dart';
import '../../core/services/task_launcher_badge.dart';

class PromyselNotificationsScreen extends StatefulWidget{
  const PromyselNotificationsScreen({super.key});
  @override State<PromyselNotificationsScreen> createState()=>_PromyselNotificationsScreenState();
}
class _PromyselNotificationsScreenState extends State<PromyselNotificationsScreen>{
  String category='all';
  final hub=PromyselNotificationHub.instance;
  @override void initState(){super.initState();unawaited(hub.refresh(force:true));}
  @override Widget build(BuildContext context)=>Scaffold(
    appBar:AppBar(title:const Text('Уведомления'),actions:[
      IconButton(tooltip:'Обновить',onPressed:()=>hub.refresh(force:true),
        icon:const Icon(Icons.refresh_rounded)),
    ]),
    body:ListenableBuilder(listenable:hub,builder:(context,_){
      final notices=hub.items.where((n)=>category=='all'||n.category==category).toList();
      const categories=<String,String>{
        'all':'Все','task':'Задания','chat':'Чаты','registration':'Персонал',
        'training':'Обучение','schedule':'График','problem':'Скважины',
      };
      return Column(children:[
        Padding(padding:const EdgeInsets.fromLTRB(12,8,12,3),
          child:Row(children:[
            const Icon(Icons.notifications_active_outlined,size:19),
            const SizedBox(width:7),
            Expanded(child:Text('Непрочитанных: '+hub.unread.toString(),
              style:const TextStyle(fontWeight:FontWeight.w600))),
            TextButton.icon(onPressed:TaskLauncherBadgeService.instance.requestPermission,
              icon:const Icon(Icons.phone_android_rounded,size:18),
              label:const Text('На телефон')),
          ])),
        if(hub.error!=null)Padding(padding:const EdgeInsets.symmetric(horizontal:15),
          child:Text(hub.error!,style:TextStyle(color:Theme.of(context).colorScheme.error))),
        SizedBox(height:42,child:ListView(
          scrollDirection:Axis.horizontal,padding:const EdgeInsets.symmetric(horizontal:10),
          children:categories.entries.map((entry)=>Padding(
            padding:const EdgeInsets.only(right:5),
            child:ChoiceChip(
              label:Text(entry.value),selected:category==entry.key,
              onSelected:(_)=>setState(()=>category=entry.key),
            ))).toList(),
        )),
        Expanded(child:RefreshIndicator(
          onRefresh:()=>hub.refresh(force:true),
          child:notices.isEmpty?
            ListView(children:const[Padding(
              padding:EdgeInsets.all(26),
              child:Center(child:Text('Новых уведомлений в этой категории нет.')))]):
            ListView.builder(
              physics:const AlwaysScrollableScrollPhysics(),
              itemCount:notices.length,
              itemBuilder:(context,index){
                final n=notices[index];
                final colors=Theme.of(context).colorScheme;
                final icon=switch(n.category){
                  'chat'=>Icons.chat_bubble_outline_rounded,
                  'training'=>Icons.school_outlined,
                  'schedule'=>Icons.calendar_month_outlined,
                  'registration'=>Icons.how_to_reg_outlined,
                  'problem'=>Icons.warning_amber_outlined,
                  _=>Icons.assignment_outlined,
                };
                return Card(
                  color:n.read?null:colors.primaryContainer.withValues(alpha:.42),
                  margin:const EdgeInsets.symmetric(horizontal:10,vertical:4),
                  child:ListTile(
                    leading:Icon(icon,size:23),
                    title:Text(n.title,style:TextStyle(
                      fontWeight:n.read?FontWeight.w500:FontWeight.w700)),
                    subtitle:Text(n.body,maxLines:3,overflow:TextOverflow.ellipsis),
                    isThreeLine:true,
                    trailing:Column(mainAxisAlignment:MainAxisAlignment.center,children:[
                      Text(n.createdAt.hour.toString().padLeft(2,'0')+':'+
                        n.createdAt.minute.toString().padLeft(2,'0'),
                        style:TextStyle(fontSize:11,color:colors.onSurfaceVariant)),
                      if(!n.read)Icon(Icons.circle,size:8,color:colors.primary),
                    ]),
                    onTap:()async{
                      final router=GoRouter.of(context);
                      unawaited(hub.markRead(n));
                      if(mounted){Navigator.of(context).pop();router.go(n.route);}
                    },
                  ),
                );
              }),
        )),
      ]);
    }),
  );
}
class PromyselNotificationOverlay extends StatelessWidget{
  const PromyselNotificationOverlay({super.key,required this.child});
  final Widget child;
  @override Widget build(BuildContext context)=>Stack(children:[
    child,
    ListenableBuilder(
      listenable:PromyselNotificationHub.instance,
      builder:(context,_){
        final hub=PromyselNotificationHub.instance,item=hub.toast;
        if(item==null)return const SizedBox.shrink();
        return Positioned(top:6,left:10,right:10,child:SafeArea(
          bottom:false,child:Material(
          borderRadius:BorderRadius.circular(14),elevation:8,
          color:Theme.of(context).colorScheme.primaryContainer,
          child:ListTile(
            leading:const Icon(Icons.notifications_active_rounded),
            title:Text(item.title,maxLines:1,overflow:TextOverflow.ellipsis,
              style:const TextStyle(fontWeight:FontWeight.w800)),
            subtitle:Text(item.body,maxLines:2,overflow:TextOverflow.ellipsis),
            trailing:IconButton(tooltip:'Закрыть',
              icon:const Icon(Icons.close_rounded),onPressed:hub.dismissToast),
            onTap:(){
              unawaited(hub.markRead(item));hub.dismissToast();
              context.go(item.route);
            },
          ),
        )));
      },
    ),
  ]);
}
