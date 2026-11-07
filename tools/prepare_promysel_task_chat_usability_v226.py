#!/usr/bin/env python3
"""v2.26: restore operator task recipients, preserve photo proportions,
refresh foreground chat previews and keep the latest bubble visible on keyboard.
Source transforms only; no database mutations or new background polling.
"""
from pathlib import Path

def replace_once(s,old,new,label):
 n=s.count(old)
 if n!=1:raise RuntimeError(f'v2.26 {label}: {n} anchors')
 return s.replace(old,new,1)

tasks=Path('lib/features/tasks/tasks_screen.dart')
s=tasks.read_text()
s=replace_once(s,
 """   final people=SessionService.instance.approvedWorkers.where(
     (x)=>x.role!=UserRole.admin&&x.id!=me.id).toList();""",
 """   final session=SessionService.instance;
   // Re-evaluate after the asynchronous personnel/presence response. A
   // snapshot captured before the request completed was stuck empty.
   List<AppUser> eligibleWorkers()=>session.approvedWorkers.where(
     (x)=>x.role!=UserRole.admin).toList();
   // Do not block the task dialog on a slow cellular connection.
   unawaited(session.refreshWorkers().catchError((Object _){ }));
   unawaited(session.refreshPresence(force:true).catchError((Object _){ }));""",
 "roster self exclusion and frozen snapshot")
s=replace_once(s,
 """     'personal'=>people.where((x)=>SessionService.instance.isAtWork(x.id)).map((x)=>(x.id,x.name+' · '+x.role.label)).toList(),""",
 """     'personal'=>eligibleWorkers().where((x)=>
       session.isAtWork(x.id)||!session.workPresence.containsKey(x.id))
       .map((x)=>(x.id,x.name+' · '+x.role.label)).toList(),""",
 "recipient choices and unknown presence")
s=replace_once(s,
 """   await showDialog<void>(context:context,builder:(ctx)=>StatefulBuilder(
     builder:(ctx,update){""",
 """   await showDialog<void>(context:context,builder:(ctx)=>ListenableBuilder(
     listenable:session,builder:(ctx,_)=>StatefulBuilder(
     builder:(ctx,update){
       // A roster response may arrive after this modal is open. Only retain a
       // selected ID when still eligible in the currently selected field.
       if(mode!='allOperators'){
         final available=options(mode);
         if(available.isNotEmpty&&!available.any((x)=>x.$1==targetId)){
           targetId=available.first.$1;targetName=available.first.$2;drafts=null;
         }else if(available.isEmpty){targetId=null;targetName='';drafts=null;}
       }""",
 "reactive task form")
s=replace_once(s,
 """     }));
   selected.dispose();title.dispose();description.dispose();""",
 """     })));
   selected.dispose();title.dispose();description.dispose();""",
 "task modal nesting")
s=replace_once(s,
 """                     if(options(mode).isEmpty)
                       const Text('Нет доступных получателей')""",
 """                     if(options(mode).isEmpty)
                       const Text('Нет получателей на работе или список '
                         'персонала ещё загружается. При наличии сети '
                         'сотрудники появятся автоматически.')""",
 "recipient empty hint")
tasks.write_text(s)

chat=Path('lib/features/chat/promysel_chat_screen.dart')
s=chat.read_text()
# The full room directory was refreshed once every 120 seconds, while unread
# global badges have their own independent refresh. Only poll when chats list
# is actually visible; room listing is cached/deduplicated by chat service.
s=replace_once(s,
 "tick=Timer.periodic(const Duration(seconds:120),(_){",
 "tick=Timer.periodic(const Duration(seconds:18),(_){",
 "chat previews 120s to 18s visible-only")
# Do not crop image content, especially spreadsheets/notes captured in the field.
# Video bubble cover remains in the separate chat_media_v198.dart.
if "fit:BoxFit.cover" not in s:
 raise RuntimeError('v2.26 expected cropped photo preview in chat screen')
s=s.replace("fit:BoxFit.cover","fit:BoxFit.contain")
# Keep image preview as an aspect-ratio-preserving scaled preview. Do not
# remove its explicit dimensions on this release; the layout has a max width.
start=s.index('class _PromyselChatRoomScreenState extends State<PromyselChatRoomScreen>{')
end=s.index('\n}\n\nString _durationLabel',start)
room=s[start:end]
room=replace_once(room,
 'class _PromyselChatRoomScreenState extends State<PromyselChatRoomScreen>{',
 'class _PromyselChatRoomScreenState extends State<PromyselChatRoomScreen> with WidgetsBindingObserver{',
 'chat room keyboard observer')
room=replace_once(room,
 ' final ChatMediaHub _mediaHub=ChatMediaHub();',
 """ final ChatMediaHub _mediaHub=ChatMediaHub();
 final FocusNode _messageFocus=FocusNode();
 void _keepLatestVisible(){
   if(!mounted||!_messageFocus.hasFocus)return;
   void scroll(){
     if(!mounted||!_messageFocus.hasFocus||!list.hasClients)return;
     final end=list.position.maxScrollExtent;
     list.animateTo(end,duration:const Duration(milliseconds:170),
       curve:Curves.easeOut);
   }
   // Wait for the browser visual viewport to shrink (Safari keyboard) and
   // then settle after the native keyboard animation. No recurring timers.
   WidgetsBinding.instance.addPostFrameCallback((_){
     scroll();
     Future<void>.delayed(const Duration(milliseconds:300),scroll);
   });
 }
 @override void didChangeMetrics(){
   super.didChangeMetrics();
   _keepLatestVisible();
 }""",
 'keyboard scroll helper')
room=replace_once(room,'super.initState();','super.initState();WidgetsBinding.instance.addObserver(this);','keyboard observer registration')
room=replace_once(room,'super.dispose();','WidgetsBinding.instance.removeObserver(this);_messageFocus.dispose();super.dispose();','keyboard observer cleanup')
room=replace_once(room,'TextField(controller:text,enabled:true,minLines:1,maxLines:4,',
 'TextField(controller:text,focusNode:_messageFocus,onTap:_keepLatestVisible,enabled:true,minLines:1,maxLines:4,',
 'composer focus hook')
s=s[:start]+room+s[end:]
chat.write_text(s)
# Explicitly preserve the full original in the dedicated task photo viewer.
photos=Path('lib/features/tasks/task_photo_widgets.dart')
p=photos.read_text()
p=replace_once(p,"Image.memory(photo.bytes,width:75,height:75,fit:BoxFit.cover)",
    "Image.memory(photo.bytes,width:75,height:75,fit:BoxFit.contain)",
    'task photo preview maintains aspect')
p=replace_once(p,
 "body:InteractiveViewer(child:Center(child:Image.network(signed,",
 "body:InteractiveViewer(child:Center(child:Image.network(signed,fit:BoxFit.contain,",
 "full task photo maintains aspect")
photos.write_text(p)
print('PASS v2.26: operator task roster, photo proportions, 18s visible-chat update, keyboard scroll')
