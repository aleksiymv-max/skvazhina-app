#!/usr/bin/env python3
"""v2.03: connect server-scoped notifications and top toast with existing Flutter shell."""
from pathlib import Path

def change(s,a,b,label):
 n=s.count(a)
 if n!=1:raise RuntimeError(f'{label}: expected one, found {n}')
 return s.replace(a,b,1)

hub=Path('lib/core/services/promysel_notification_hub.dart')
ui=Path('lib/features/notifications/promysel_notifications_screen.dart')
assert not hub.exists() and not ui.exists()
hub.write_text(Path(__file__).with_name('promysel_notification_hub_v203.dart')
    .read_text(encoding='utf-8'),encoding='utf-8')
ui.parent.mkdir(parents=True,exist_ok=True)
ui.write_text(Path(__file__).with_name('promysel_notification_center_v203.dart')
    .read_text(encoding='utf-8'),encoding='utf-8')

p=Path('lib/app/app.dart');s=p.read_text(encoding='utf-8')
s="import '../core/services/promysel_notification_hub.dart';\n"+s
s="import '../features/notifications/promysel_notifications_screen.dart';\n"+s
s=change(s,'PromyselChatUnread.instance.start();return Scaffold(',
  'PromyselChatUnread.instance.start();PromyselNotificationHub.instance.start();return Scaffold(',
  'one notification controller per authenticated app shell')
s=change(s,'body:RepaintBoundary(child:TaskNotificationOnboarding(child:shell)),',
  'body:RepaintBoundary(child:PromyselNotificationOverlay(child:TaskNotificationOnboarding(child:shell))),',
  'one top toast overlay')
p.write_text(s,encoding='utf-8')

p=Path('lib/features/menu/menu_screen.dart');s=p.read_text(encoding='utf-8')
s="import '../../core/services/promysel_notification_hub.dart';\n"+s
s="import '../notifications/promysel_notifications_screen.dart';\n"+s
anchor="_entry(context,Icons.menu_book_outlined,'Документация',"
insert="""ListenableBuilder(
     listenable:PromyselNotificationHub.instance,
     builder:(context,_){
       final count=PromyselNotificationHub.instance.unread;
       return Card(child:ListTile(
         leading:Badge(isLabelVisible:count>0,
           label:Text(count>99?'99+':count.toString()),
           child:const Icon(Icons.notifications_active_outlined)),
         title:const Text('Уведомления'),
         subtitle:Text(count>0?'Непрочитанных: '+count.toString():
           'Задания, чаты, график, обучение и проблемы'),
         trailing:const Icon(Icons.chevron_right_rounded),
         onTap:()=>Navigator.of(context).push(MaterialPageRoute<void>(
           builder:(_)=>const PromyselNotificationsScreen())),
       ));
     }),
   """
s=change(s,anchor,insert+anchor,'center entry accessible in menu')
p.write_text(s,encoding='utf-8')

p=Path('lib/core/services/task_notification_onboarding.dart')
s=p.read_text(encoding='utf-8')
s=change(s,"'Уведомления о заданиях'","'Уведомления «Промысла»'",'permission headline')
s=change(s,"'Разрешите уведомления, чтобы видеть новые задания и их выполнение '",
         "'Разрешите уведомления, чтобы получать сообщения, задания, обучение и изменения графика '",
         'explain more categories')
s=change(s,'promysel_push_permission_prompt_v2_','promysel_push_permission_prompt_v3_',
         'request permission once for renewed categories')
p.write_text(s,encoding='utf-8')
print('PASS v2.03 Flutter: one server-scoped feed, centered notification history, top alerts, permission onboarding')
