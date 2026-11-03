import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'session_service.dart';
import 'task_launcher_badge.dart';

/// First-login opt-in. iOS WebKit requires the OS permission request to be
/// initiated by a tap; never call Notification.requestPermission on startup.
class TaskNotificationOnboarding extends StatefulWidget {
  const TaskNotificationOnboarding({super.key,required this.child});
  final Widget child;
  @override
  State<TaskNotificationOnboarding> createState()=>_TaskNotificationOnboardingState();
}
class _TaskNotificationOnboardingState extends State<TaskNotificationOnboarding> {
  String? _lastChecked;
  bool _dialogOpen=false;
  @override
  void initState() {
    super.initState();
    SessionService.instance.addListener(_check);
    WidgetsBinding.instance.addPostFrameCallback((_) => _check());
  }
  void _check() {
    if(!mounted||_dialogOpen)return;
    final user=SessionService.instance.currentUser;
    if(user.id.isEmpty||!user.approved||_lastChecked==user.id)return;
    _lastChecked=user.id;
    WidgetsBinding.instance.addPostFrameCallback((_) => _offer(user.id));
  }
  Future<void> _offer(String userId) async {
    if(!mounted||_dialogOpen||SessionService.instance.currentUser.id!=userId)return;
    final prefs=await SharedPreferences.getInstance();
    final key='promysel_push_permission_prompt_v1_$userId';
    if(!mounted||_dialogOpen||prefs.getBool(key)==true)return;
    _dialogOpen=true;
    // Record one presentation, not repeated requests on every navigation.
    await prefs.setBool(key,true);
    if(!mounted){_dialogOpen=false;return;}
    await showDialog<void>(
      context:context,
      builder:(ctx)=>AlertDialog(
        title:const Text('Уведомления о заданиях'),
        content:const Text(
          'Разрешите уведомления, чтобы видеть новые задания и их выполнение '
          'на телефоне и значке приложения. На iPhone веб-приложение должно '
          'быть установлено на экран «Домой». Разрешение можно включить '
          'позже в разделе «Уведомления».'),
        actions:[
          TextButton(
            onPressed:()=>Navigator.pop(ctx),
            child:const Text('Не сейчас'),
          ),
          FilledButton.icon(
            icon:const Icon(Icons.notifications_active_outlined),
            onPressed:(){
              // Must happen immediately inside the button's tap handler.
              TaskLauncherBadgeService.instance.requestPermission();
              Navigator.pop(ctx);
            },
            label:const Text('Разрешить уведомления'),
          ),
        ],
      ),
    );
    _dialogOpen=false;
  }
  @override
  void dispose(){
    SessionService.instance.removeListener(_check);
    super.dispose();
  }
  @override
  Widget build(BuildContext context)=>widget.child;
}
