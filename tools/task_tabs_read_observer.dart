import 'dart:async';
import 'package:flutter/material.dart';
import '../../core/services/notification_store.dart';
import '../../core/services/session_service.dart';

/// Task inbox tabs do not need a separate notification inbox. A notice becomes
/// read when its relevant tab is actually visible. TickerMode prevents an
/// offstage, cached GoRouter shell tab from silently reading notifications.
class TaskTabsReadObserver extends StatefulWidget {
  const TaskTabsReadObserver({super.key, required this.child});
  final Widget child;
  @override
  State<TaskTabsReadObserver> createState() => _TaskTabsReadObserverState();
}
class _TaskTabsReadObserverState extends State<TaskTabsReadObserver> {
  TabController? _controller;
  bool _scheduled=false;
  @override void initState(){
    super.initState();
    NotificationStore.instance.addListener(_scheduleRead);
    SessionService.instance.addListener(_scheduleRead);
  }
  @override void didChangeDependencies(){
    super.didChangeDependencies();
    final next=DefaultTabController.of(context);
    if(!identical(next,_controller)){
      _controller?.removeListener(_scheduleRead);
      _controller=next;
      next.addListener(_scheduleRead);
    }
    _scheduleRead();
  }
  void _scheduleRead(){
    if(!mounted||_scheduled)return;
    _scheduled=true;
    WidgetsBinding.instance.addPostFrameCallback((_){
      _scheduled=false;
      if(!mounted||!TickerMode.of(context))return;
      final index=_controller?.index??0;
      final category=switch(index){0=>'personal',1=>'common',_=>'issued'};
      final session=SessionService.instance;
      final userId=session.currentUser.id;
      if(userId.isNotEmpty &&
         NotificationStore.instance.unreadCategory(userId,category)>0){
        unawaited(NotificationStore.instance.markCategoryRead(userId,category));
      }
    });
  }
  @override void dispose(){
    _controller?.removeListener(_scheduleRead);
    NotificationStore.instance.removeListener(_scheduleRead);
    SessionService.instance.removeListener(_scheduleRead);
    super.dispose();
  }
  @override Widget build(BuildContext context)=>widget.child;
}
