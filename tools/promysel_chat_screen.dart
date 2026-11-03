import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';
import 'package:image_picker/image_picker.dart';
import 'package:file_picker/file_picker.dart';
import 'package:record/record.dart';
import 'package:path_provider/path_provider.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../core/services/session_service.dart';
import '../../core/services/promysel_chat_service.dart';

final _chat=PromyselChatService.instance;
String _date(dynamic v){final d=DateTime.tryParse('${v??''}')?.toLocal();return d==null?'':DateFormat('dd.MM HH:mm').format(d);}
String _time(dynamic v){final d=DateTime.tryParse('${v??''}')?.toLocal();return d==null?'':DateFormat('HH:mm').format(d);}
String _name(Map<String,dynamic> room){
  if(room['kind']=='saved')return 'Избранное';
  if(room['kind']=='group')return '${room['title']??'Группа'}';
  final other=((room['people'] as List?)??[]).whereType<Map>().where((p)=>p['id']!=_chat.userId);
  return other.isEmpty?'Личный чат':'${other.first['name']??'Сотрудник'}';
}
String _preview(Map<String,dynamic>? m){if(m==null)return 'Сообщений пока нет';if(m['deleted_at']!=null)return 'Сообщение удалено';return switch(m['kind']){
  'image'=>'📷 Фото', 'video'=>'🎬 Видео', 'voice'=>'🎤 Голосовое сообщение','document'=>'📎 Документ',_=>'${m['body']??''}'
};}

class PromyselChatScreen extends StatefulWidget{
 const PromyselChatScreen({super.key});
 @override State<PromyselChatScreen> createState()=>_PromyselChatScreenState();
}
class _PromyselChatScreenState extends State<PromyselChatScreen>{
 List<Map<String,dynamic>> rooms=[];bool loading=true;String? error;String search='';Timer? tick;int knownUnread=-1;bool busy=false;
 @override void initState(){super.initState();_load();tick=Timer.periodic(const Duration(seconds:12),(_)=>_load(silent:true));}
 @override void dispose(){tick?.cancel();super.dispose();}
 Future<void> _load({bool silent=false})async{
   if(!mounted)return;
   try{final next=await _chat.rooms();if(!mounted)return;
     final total=next.where((r)=>r['muted']!=true).fold<int>(0,(a,r)=>a+((r['unread'] as num?)?.toInt()??0));
     // The global unread monitor handles sound and badges without duplicate alerts.
     setState((){rooms=next;loading=false;error=null;knownUnread=total;});
   }catch(e){if(mounted)setState((){loading=false;error='$e';});}
 }
 Future<void> _create(String kind,{String? personId,String title='',List<String> ids=const []})async{
   if(busy)return;setState(()=>busy=true);
   try{final id=await _chat.create(kind,people:personId==null?ids:[personId],title:title);
     await _load();if(mounted)context.go('/chat/$id');
   }catch(e){_report(e);}finally{if(mounted)setState(()=>busy=false);}
 }
 void _report(Object e){if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(e.toString().replaceFirst('Exception: ',''))));}
 Future<void> _pickPerson({bool group=false})async{
   try{final people=(await _chat.users()).where((x)=>x['id']!=_chat.userId).toList();
     if(!mounted)return;
     if(group){await _groupDialog(people);return;}
     await showModalBottomSheet<void>(context:context,isScrollControlled:true,showDragHandle:true,builder:(sheet)=>SafeArea(child:FractionallySizedBox(heightFactor:.65,child:Column(children:[
       const Padding(padding:EdgeInsets.all(16),child:Text('Новый личный чат',style:TextStyle(fontSize:19,fontWeight:FontWeight.w800))),
       Expanded(child:ListView(children:[for(final p in people)ListTile(leading:const CircleAvatar(child:Icon(Icons.person_outline)),title:Text('${p['name']}'),onTap:(){Navigator.pop(sheet);_create('private',personId:'${p['id']}');})])),
     ]))));
   }catch(e){_report(e);}
 }
 Future<void> _groupDialog(List<Map<String,dynamic>> people)async{
   final title=TextEditingController();final chosen=<String>{};
   await showDialog<void>(context:context,builder:(d)=>StatefulBuilder(builder:(d,refresh)=>AlertDialog(
     title:const Text('Новая группа'),content:SizedBox(width:400,height:400,child:Column(children:[
       TextField(controller:title,maxLength:80,decoration:const InputDecoration(labelText:'Название группы',border:OutlineInputBorder())),
       const Align(alignment:Alignment.centerLeft,child:Text('Участники',style:TextStyle(fontWeight:FontWeight.w700))),
       Expanded(child:ListView(children:[for(final p in people)CheckboxListTile(dense:true,title:Text('${p['name']}'),
         value:chosen.contains('${p['id']}'),onChanged:(v)=>refresh((){if(v==true)chosen.add('${p['id']}');else chosen.remove('${p['id']}');})]))
     ])),actions:[TextButton(onPressed:()=>Navigator.pop(d),child:const Text('Отмена')),
       FilledButton(onPressed:(){if(title.text.trim().isEmpty||chosen.isEmpty)return;Navigator.pop(d);_create('group',ids:chosen.toList(),title:title.text.trim());},child:const Text('Создать'))],
   )));title.dispose();
 }
 Future<void> _settings()async{
   bool sound=await _chat.soundEnabled();if(!mounted)return;
   await showDialog<void>(context:context,builder:(d)=>StatefulBuilder(builder:(d,refresh)=>AlertDialog(
     title:const Text('Настройки чатов'),content:Column(mainAxisSize:MainAxisSize.min,children:[
       SwitchListTile(contentPadding:EdgeInsets.zero,title:const Text('Звук новых сообщений'),subtitle:const Text('При открытом приложении'),value:sound,
         onChanged:(v)async{await _chat.setSound(v);refresh(()=>sound=v);}),
       ListTile(contentPadding:EdgeInsets.zero,leading:const Icon(Icons.storage_outlined),title:const Text('Очистить кэш'),
         subtitle:Text('Изображения: ${(PaintingBinding.instance.imageCache.currentSizeBytes/1024/1024).toStringAsFixed(1)} МБ · сообщения остаются на сервере'),onTap:()async{
           PaintingBinding.instance.imageCache.clear();PaintingBinding.instance.imageCache.clearLiveImages();
           if(d.mounted)ScaffoldMessenger.of(d).showSnackBar(const SnackBar(content:Text('Кэш изображений очищен')));
         }),
     ]),actions:[TextButton(onPressed:()=>Navigator.pop(d),child:const Text('Готово'))],
   )));
 }
 @override Widget build(BuildContext context){
   final filtered=rooms.where((r)=>_name(r).toLowerCase().contains(search.toLowerCase())||_preview(r['last'] is Map?Map<String,dynamic>.from(r['last']):null).toLowerCase().contains(search.toLowerCase())).toList();
   return Scaffold(appBar:AppBar(leading:IconButton(tooltip:'Назад в меню',icon:const Icon(Icons.arrow_back),onPressed:()=>context.go('/menu')),
     title:const Text('Чаты'),actions:[IconButton(tooltip:'Настройки чата',onPressed:_settings,icon:const Icon(Icons.settings_outlined)),
       IconButton(tooltip:'Обновить',onPressed:_load,icon:const Icon(Icons.refresh))]),
     floatingActionButton:FloatingActionButton.extended(onPressed:busy?null:()=>_pickPerson(),icon:const Icon(Icons.chat_bubble_outline),label:const Text('Написать')),
     body:Column(children:[Padding(padding:const EdgeInsets.fromLTRB(12,8,12,0),child:TextField(onChanged:(v)=>setState(()=>search=v),
       decoration:InputDecoration(hintText:'Поиск по чатам',prefixIcon:const Icon(Icons.search),filled:true,border:OutlineInputBorder(borderRadius:BorderRadius.circular(15),borderSide:BorderSide.none)))),
       Padding(padding:const EdgeInsets.fromLTRB(12,6,12,6),child:Row(children:[
         TextButton.icon(onPressed:busy?null:()=>_create('saved'),icon:const Icon(Icons.bookmark_border),label:const Text('Избранное')),
         const SizedBox(width:8),TextButton.icon(onPressed:busy?null:()=>_pickPerson(group:true),icon:const Icon(Icons.group_add_outlined),label:const Text('Новая группа')),
       ])),
       if(error!=null)Padding(padding:const EdgeInsets.symmetric(horizontal:12),child:Text(error!,style:TextStyle(color:Theme.of(context).colorScheme.error))),
       if(loading)const LinearProgressIndicator(),
       Expanded(child:RefreshIndicator(onRefresh:_load,child:filtered.isEmpty?ListView(children:[const SizedBox(height:80),Center(child:Text('Чатов пока нет. Создайте личный чат или группу.'))]):ListView.builder(itemCount:filtered.length,itemBuilder:(context,i){
         final r=filtered[i],last=r['last'] is Map?Map<String,dynamic>.from(r['last']):null,unread=(r['unread'] as num?)?.toInt()??0;
         return ListTile(leading:CircleAvatar(backgroundImage:r['avatarUrl'] is String&&('${r['avatarUrl']}').isNotEmpty?NetworkImage('${r['avatarUrl']}'):null,child:r['avatarUrl'] is String&&('${r['avatarUrl']}').isNotEmpty?null:Icon(r['kind']=='saved'?Icons.bookmark_outline:r['kind']=='group'?Icons.group_outlined:Icons.person_outline)),
           title:Text(_name(r),maxLines:1,overflow:TextOverflow.ellipsis,style:TextStyle(fontWeight:unread>0?FontWeight.w800:FontWeight.w600)),
           subtitle:Text(_preview(last),maxLines:1,overflow:TextOverflow.ellipsis),
           trailing:Column(mainAxisAlignment:MainAxisAlignment.center,children:[Text(_time(last?['created_at']),style:Theme.of(context).textTheme.labelSmall),
             if(unread>0)Badge(label:Text(unread>99?'99+':'$unread'))else if(r['muted']==true)const Icon(Icons.notifications_off_outlined,size:17)]),
           onTap:()=>context.go('/chat/${r['id']}'),
         );
       }))),
     ]),
   );
 }
}

class PromyselChatRoomScreen extends StatefulWidget{
 const PromyselChatRoomScreen({super.key,required this.roomId});final String roomId;
 @override State<PromyselChatRoomScreen> createState()=>_PromyselChatRoomScreenState();
}
class _PromyselChatRoomScreenState extends State<PromyselChatRoomScreen>{
 final text=TextEditingController(),list=ScrollController(),recorder=AudioRecorder();
 List<Map<String,dynamic>> messages=[];Map<String,dynamic>? room;Timer? tick;int polls=0;bool loading=true,busy=false,recording=false;
 String search='';
 @override void initState(){super.initState();_init();tick=Timer.periodic(const Duration(seconds:5),(_){_refresh(silent:true);if(++polls%3==0)_reloadRoom();});}
 @override void dispose(){tick?.cancel();text.dispose();list.dispose();recorder.dispose();super.dispose();}
 Future<void> _init()async{
   try{final rooms=await _chat.rooms();room=rooms.where((r)=>r['id']==widget.roomId).firstOrNull;await _refresh();}
   catch(e){_report(e);if(mounted)setState(()=>loading=false);}
 }
 Future<void> _refresh({bool silent=false})async{
   if(busy)return;
   try{final next=await _chat.messages(widget.roomId);if(!mounted)return;
     final changed=messages.isEmpty||next.length!=messages.length||next.lastOrNull?['id']!=messages.lastOrNull?['id']||
       (next.isNotEmpty&&messages.isNotEmpty&&next.last['body']!=messages.last['body']);
     if(changed)setState((){messages=next;loading=false;});else if(loading)setState(()=>loading=false);
     final lastReceived=next.where((x)=>x['sender_id']!=_chat.userId).lastOrNull;
     final latestAt=DateTime.tryParse('${lastReceived?['created_at']??''}');
     final readAt=DateTime.tryParse('${room?['lastReadAt']??''}');
     if(latestAt!=null&&(readAt==null||latestAt.isAfter(readAt))){
       await _chat.settings(widget.roomId,read:true);if(room!=null)room!['lastReadAt']=DateTime.now().toUtc().toIso8601String();
     }
     if(next.isNotEmpty){
       if(changed&&!silent)WidgetsBinding.instance.addPostFrameCallback((_){if(list.hasClients)list.jumpTo(list.position.maxScrollExtent);});}
   }catch(e){if(!silent)_report(e);if(mounted)setState(()=>loading=false);}
 }
 void _report(Object e){if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(e.toString().replaceFirst('Exception: ',''))));}
 Future<void> _send()async{
   final value=text.text.trim();if(value.isEmpty||busy)return;
   text.clear();setState(()=>busy=true);
   try{await _chat.sendText(widget.roomId,value);}
   catch(e){text.text=value;_report(e);}
   finally{if(mounted){setState(()=>busy=false);await _refresh();}}
 }
 Future<void> _media(XFile file,String kind)async{
   if(busy)return;setState(()=>busy=true);
   try{await _chat.sendMedia(widget.roomId,file,kind);await _refresh();}
   catch(e){_report(e);}finally{if(mounted)setState(()=>busy=false);}
 }
 Future<void> _attachment(String kind,{bool camera=false})async{
   try{
     if(kind=='document'){
       final picked=await FilePicker.platform.pickFiles(type:FileType.any,withData:true);
       if(picked!=null){for(final f in picked.xFiles){await _media(f,'document');}}
     }else if(kind=='image'){
       if(camera){final x=await ImagePicker().pickImage(source:ImageSource.camera,imageQuality:80,maxWidth:2200);if(x!=null)await _media(x,'image');}
       else{final xs=await ImagePicker().pickMultiImage(imageQuality:80,maxWidth:2200);for(final x in xs)await _media(x,'image');}
     }else if(kind=='video'){
       final x=await ImagePicker().pickVideo(source:camera?ImageSource.camera:ImageSource.gallery,maxDuration:const Duration(minutes:2));if(x!=null)await _media(x,'video');
     }
   }catch(e){_report(e);}
 }
 Future<void> _startOrStopVoice()async{
   try{
     if(recording){final file=await recorder.stop();setState(()=>recording=false);if(file!=null&&file.isNotEmpty)await _media(XFile(file,name:kIsWeb?'voice.webm':'voice.m4a'),'voice');return;}
     final allowed=await recorder.hasPermission();if(!allowed){_report('Разрешите доступ к микрофону');return;}
     final stamp=DateTime.now().microsecondsSinceEpoch;
     final path=kIsWeb?'voice_$stamp.webm':'${(await getTemporaryDirectory()).path}/voice_$stamp.m4a';
     await recorder.start(RecordConfig(encoder:kIsWeb?AudioEncoder.opus:AudioEncoder.aacLc),path:path);
     if(mounted)setState(()=>recording=true);
   }catch(e){if(mounted)setState(()=>recording=false);_report(e);}
 }
 Future<void> _attachMenu()async{
   await showModalBottomSheet<void>(context:context,showDragHandle:true,builder:(sheet)=>SafeArea(child:Wrap(children:[
     ListTile(leading:const Icon(Icons.photo_library_outlined),title:const Text('Фото из галереи'),onTap:(){Navigator.pop(sheet);_attachment('image');}),
     ListTile(leading:const Icon(Icons.camera_alt_outlined),title:const Text('Снять фото'),onTap:(){Navigator.pop(sheet);_attachment('image',camera:true);}),
     ListTile(leading:const Icon(Icons.videocam_outlined),title:const Text('Снять видеосообщение'),onTap:(){Navigator.pop(sheet);_attachment('video',camera:true);}),
     ListTile(leading:const Icon(Icons.video_library_outlined),title:const Text('Видео из галереи'),onTap:(){Navigator.pop(sheet);_attachment('video');}),
     ListTile(leading:const Icon(Icons.attach_file),title:const Text('Документ'),onTap:(){Navigator.pop(sheet);_attachment('document');}),
   ])));
 }
 Future<void> _messageAction(Map<String,dynamic> m)async{
   if(m['sender_id']!=_chat.userId||m['deleted_at']!=null)return;
   await showModalBottomSheet<void>(context:context,showDragHandle:true,builder:(sheet)=>SafeArea(child:Wrap(children:[
     if(m['kind']=='text')ListTile(leading:const Icon(Icons.edit_outlined),title:const Text('Редактировать'),onTap:(){Navigator.pop(sheet);_edit(m);}),
     ListTile(leading:const Icon(Icons.delete_outline),title:const Text('Удалить у всех'),onTap:(){Navigator.pop(sheet);_delete(m);}),
   ])));
 }
 Future<void> _edit(Map<String,dynamic> m)async{
   final control=TextEditingController(text:'${m['body']??''}');
   final ok=await showDialog<bool>(context:context,builder:(d)=>AlertDialog(title:const Text('Изменить сообщение'),content:TextField(controller:control,maxLines:4,maxLength:8000),actions:[
     TextButton(onPressed:()=>Navigator.pop(d,false),child:const Text('Отмена')),
     FilledButton(onPressed:()=>Navigator.pop(d,true),child:const Text('Сохранить'))]));
   final value=control.text.trim();control.dispose();if(ok!=true||value.isEmpty)return;
   try{await _chat.changeMessage(widget.roomId,'${m['id']}',value);await _refresh();}catch(e){_report(e);}
 }
 Future<void> _delete(Map<String,dynamic> m)async{
   final ok=await showDialog<bool>(context:context,builder:(d)=>AlertDialog(title:const Text('Удалить сообщение?'),content:const Text('Сообщение станет недоступно всем участникам.'),actions:[
     TextButton(onPressed:()=>Navigator.pop(d,false),child:const Text('Отмена')),
     FilledButton(onPressed:()=>Navigator.pop(d,true),child:const Text('Удалить'))]));
   if(ok!=true)return;try{await _chat.deleteMessage(widget.roomId,'${m['id']}');await _refresh();}catch(e){_report(e);}
 }
 Future<void> _openUrl(String value)async{
   if(value.isEmpty)return;
   try{if(!await launchUrl(Uri.parse(value),mode:LaunchMode.externalApplication))throw Exception('Не удалось открыть вложение');}catch(e){_report(e);}
 }
 Widget _bubble(Map<String,dynamic> m){
   final mine=m['sender_id']==_chat.userId,deleted=m['deleted_at']!=null,kind='${m['kind']??'text'}',url='${m['url']??''}';
   final people=((room?['people'] as List?)??[]).whereType<Map>();
   final who=mine?'Вы':people.where((p)=>p['id']==m['sender_id']).map((p)=>'${p['name']}').firstOrNull??'Сотрудник';
   final others=people.where((p)=>p['id']!=_chat.userId).toList();
   final time=DateTime.tryParse('${m['created_at']??''}');
   final read=mine&&time!=null&&others.isNotEmpty&&others.every((p){final at=DateTime.tryParse('${p['readAt']??''}');return at!=null&&!at.isBefore(time);});
   return Align(alignment:mine?Alignment.centerRight:Alignment.centerLeft,child:ConstrainedBox(constraints:const BoxConstraints(maxWidth:330),child:GestureDetector(
     onLongPress:()=>_messageAction(m),child:Container(margin:const EdgeInsets.symmetric(horizontal:10,vertical:4),padding:const EdgeInsets.fromLTRB(12,9,12,7),
       decoration:BoxDecoration(color:mine?Theme.of(context).colorScheme.primaryContainer:Theme.of(context).colorScheme.surfaceContainerHighest,borderRadius:BorderRadius.circular(16)),
       child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[
         if(room?['kind']=='group'&&!mine)Padding(padding:const EdgeInsets.only(bottom:3),child:Text(who,style:const TextStyle(fontSize:12,fontWeight:FontWeight.w800))),
         if(deleted)const Text('Сообщение удалено',style:TextStyle(fontStyle:FontStyle.italic)),
         if(!deleted&&kind=='image'&&url.isNotEmpty)GestureDetector(onTap:()=>showDialog<void>(context:context,builder:(d)=>Dialog(child:InteractiveViewer(child:Image.network(url)))),
           child:ClipRRect(borderRadius:BorderRadius.circular(10),child:Image.network(url,width:250,height:180,fit:BoxFit.cover,errorBuilder:(_,__,___)=>const Text('Не удалось загрузить фото')))),
         if(!deleted&&kind=='voice')TextButton.icon(onPressed:()=>_openUrl(url),icon:const Icon(Icons.play_circle_outline),label:const Text('Прослушать голосовое')),
         if(!deleted&&kind=='video')TextButton.icon(onPressed:()=>_openUrl(url),icon:const Icon(Icons.play_arrow),label:const Text('Открыть видеосообщение')),
         if(!deleted&&kind=='document')TextButton.icon(onPressed:()=>_openUrl(url),icon:const Icon(Icons.insert_drive_file_outlined),label:Text('${m['attachment_name']??'Документ'}',maxLines:2,overflow:TextOverflow.ellipsis)),
         if(!deleted&&'${m['body']??''}'.isNotEmpty)Text('${m['body']}',style:const TextStyle(fontSize:15)),
         Align(alignment:Alignment.centerRight,child:Text('${m['edited_at']!=null?'изменено · ':''}${_time(m['created_at'])}${mine?(read?' ✓✓':' ✓'):''}',style:Theme.of(context).textTheme.labelSmall)),
       ])),
   ))));
 }
 Future<void> _roomSettings()async{
   if(room==null)return;final r=room!;bool muted=r['muted']==true,sound=r['soundEnabled']!=false;
   await showDialog<void>(context:context,builder:(d)=>StatefulBuilder(builder:(d,refresh)=>AlertDialog(title:Text(_name(r)),content:SizedBox(width:420,child:SingleChildScrollView(child:Column(mainAxisSize:MainAxisSize.min,crossAxisAlignment:CrossAxisAlignment.start,children:[
     SwitchListTile(title:const Text('Без уведомлений'),value:muted,onChanged:(v)async{try{await _chat.settings(widget.roomId,muted:v);refresh(()=>muted=v);setState(()=>r['muted']=v);}catch(e){_report(e);}}),
     SwitchListTile(title:const Text('Звук сообщений'),value:sound,onChanged:(v)async{try{await _chat.settings(widget.roomId,soundEnabled:v);refresh(()=>sound=v);setState(()=>r['soundEnabled']=v);}catch(e){_report(e);}}),
     if(r['kind']=='group')...[const Divider(),const Text('Участники',style:TextStyle(fontWeight:FontWeight.w800)),
       for(final p in ((r['people'] as List?)??[]).whereType<Map>())ListTile(dense:true,title:Text('${p['name']}'),
         trailing:r['created_by']==_chat.userId&&p['id']!=_chat.userId?IconButton(icon:const Icon(Icons.person_remove_outlined),onPressed:()async{try{await _chat.member(widget.roomId,'${p['id']}',add:false);await _reloadRoom();refresh((){});}catch(e){_report(e);}}):null),
       if(r['created_by']==_chat.userId)...[
         TextButton.icon(icon:const Icon(Icons.add_a_photo_outlined),label:const Text('Фотография группы'),onPressed:(){Navigator.pop(d);_changeAvatar();}),
         TextButton.icon(icon:const Icon(Icons.person_add_outlined),label:const Text('Добавить участника'),onPressed:()async{Navigator.pop(d);await _addMember();}),
         TextButton.icon(icon:const Icon(Icons.edit_outlined),label:const Text('Переименовать группу'),onPressed:(){Navigator.pop(d);_renameGroup();}),
       ]else TextButton.icon(icon:const Icon(Icons.exit_to_app),label:const Text('Покинуть группу'),onPressed:()async{Navigator.pop(d);await _leave();}),
     ],
   ]))),actions:[TextButton(onPressed:()=>Navigator.pop(d),child:const Text('Закрыть'))])));
 }
 Future<void> _reloadRoom()async{final rooms=await _chat.rooms();final next=rooms.where((x)=>x['id']==widget.roomId).firstOrNull;if(mounted)setState(()=>room=next);}
 Future<void> _changeAvatar()async{
   try{final image=await ImagePicker().pickImage(source:ImageSource.gallery,imageQuality:80,maxWidth:1200);
     if(image==null)return;await _chat.groupAvatar(widget.roomId,image);await _reloadRoom();
   }catch(e){_report(e);}
 }
 Future<void> _addMember()async{
   try{final existing=((room?['people'] as List?)??[]).whereType<Map>().map((x)=>'${x['id']}').toSet();
     final people=(await _chat.users()).where((p)=>!existing.contains('${p['id']}')).toList();if(!mounted)return;
     await showModalBottomSheet<void>(context:context,showDragHandle:true,builder:(d)=>SafeArea(child:ListView(shrinkWrap:true,children:[
       const Padding(padding:EdgeInsets.all(16),child:Text('Добавить в группу',style:TextStyle(fontWeight:FontWeight.w800,fontSize:19))),
       for(final p in people)ListTile(title:Text('${p['name']}'),onTap:()async{Navigator.pop(d);try{await _chat.member(widget.roomId,'${p['id']}',add:true);await _reloadRoom();}catch(e){_report(e);}})
     ])));
   }catch(e){_report(e);}
 }
 Future<void> _renameGroup()async{
   final c=TextEditingController(text:'${room?['title']??''}');
   final ok=await showDialog<bool>(context:context,builder:(d)=>AlertDialog(title:const Text('Название группы'),content:TextField(controller:c,maxLength:100),actions:[TextButton(onPressed:()=>Navigator.pop(d,false),child:const Text('Отмена')),FilledButton(onPressed:()=>Navigator.pop(d,true),child:const Text('Сохранить'))]));
   final n=c.text.trim();c.dispose();if(ok==true&&n.isNotEmpty){try{await _chat.settings(widget.roomId,title:n);await _reloadRoom();}catch(e){_report(e);}}
 }
 Future<void> _leave()async{
   try{await _chat.leave(widget.roomId);if(mounted)context.go('/chat');}catch(e){_report(e);}
 }
 @override Widget build(BuildContext context){
   final visible=messages.where((m)=>search.isEmpty||'${m['body']??''}'.toLowerCase().contains(search.toLowerCase())).toList();
   return Scaffold(appBar:AppBar(leading:IconButton(tooltip:'К списку чатов',icon:const Icon(Icons.arrow_back),onPressed:()=>context.go('/chat')),
     title:Text(room==null?'Переписка':_name(room!),maxLines:1,overflow:TextOverflow.ellipsis),actions:[
       IconButton(tooltip:'Поиск сообщений',onPressed:()async{final c=TextEditingController(text:search);
         final value=await showDialog<String>(context:context,builder:(d)=>AlertDialog(title:const Text('Поиск в чате'),content:TextField(controller:c,autofocus:true),actions:[TextButton(onPressed:()=>Navigator.pop(d,''),child:const Text('Очистить')),FilledButton(onPressed:()=>Navigator.pop(d,c.text),child:const Text('Найти'))]));
         c.dispose();if(value!=null&&mounted)setState(()=>search=value);
       },icon:const Icon(Icons.search)),IconButton(tooltip:'Настройки беседы',onPressed:_roomSettings,icon:const Icon(Icons.more_vert))]),
     body:Column(children:[if(loading)const LinearProgressIndicator(),
       Expanded(child:visible.isEmpty?Center(child:Text(loading?'Загрузка…':search.isNotEmpty?'Ничего не найдено':'Напишите первое сообщение')):
         ListView.builder(controller:list,padding:const EdgeInsets.symmetric(vertical:9),itemCount:visible.length,itemBuilder:(_,i)=>_bubble(visible[i]))),
       if(recording)Container(color:Theme.of(context).colorScheme.errorContainer,padding:const EdgeInsets.all(7),child:const Row(mainAxisAlignment:MainAxisAlignment.center,children:[Icon(Icons.mic,color:Colors.red),SizedBox(width:6),Text('Идёт запись голосового сообщения · нажмите ещё раз для отправки')])),
       SafeArea(top:false,child:Padding(padding:const EdgeInsets.fromLTRB(6,6,6,6),child:Row(children:[
         IconButton(tooltip:'Прикрепить файл',onPressed:busy?null:_attachMenu,icon:const Icon(Icons.add_circle_outline)),
         Expanded(child:TextField(controller:text,enabled:!busy,minLines:1,maxLines:4,textCapitalization:TextCapitalization.sentences,
           onSubmitted:(_)=>_send(),decoration:InputDecoration(hintText:'Сообщение',isDense:true,filled:true,border:OutlineInputBorder(borderRadius:BorderRadius.circular(22),borderSide:BorderSide.none)))),
         IconButton(tooltip:recording?'Завершить запись':'Голосовое сообщение',onPressed:busy?null:_startOrStopVoice,
           icon:Icon(recording?Icons.stop_circle_outlined:Icons.mic_none,color:recording?Colors.red:null)),
         IconButton(tooltip:'Отправить',onPressed:busy?null:_send,icon:const Icon(Icons.send_rounded)),
       ]))),
     ]));
 }
}