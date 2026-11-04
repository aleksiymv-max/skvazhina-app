#!/usr/bin/env python3
"""Chat v1.89: messenger-style UI, bounded repaints and parallel cold loading.

Runs after the existing v1.88 source transforms. Shared by Web and Android;
no API changes, database writes or platform-specific widgets.
"""
from pathlib import Path

p=Path('lib/features/chat/promysel_chat_screen.dart')
s=p.read_text(encoding='utf-8')

def replace_once(old,new,label):
    global s
    found=s.count(old)
    if found!=1:
        raise RuntimeError(f'{label}: expected exactly one anchor, got {found}')
    s=s.replace(old,new,1)

replace_once("String _name(Map<String,dynamic> room){", """String _dayKey(dynamic raw){
  final d=DateTime.tryParse('4{raw??''}')?.toLocal();
  if(d==null)return '';
  return '4{d.year.toString().padLeft(4,'0')}-4{d.month.toString().padLeft(2,'0')}-4{d.day.toString().padLeft(2,'0')}';
}
String _dayTitle(dynamic raw){
  final d=DateTime.tryParse('4{raw??''}')?.toLocal();
  if(d==null)return '';
  final today=DateTime.now();
  final midnight=DateTime(today.year,today.month,today.day);
  final day=DateTime(d.year,d.month,d.day);
  if(day==midnight)return 'Сегодня';
  if(day==midnight.subtract(const Duration(days:1)))return 'Вчера';
  return DateFormat('dd.MM.yyyy').format(d);
}
bool _sameMessagePage(List<Map<String,dynamic>> old,List<Map<String,dynamic>> next){
  if(old.length!=next.length)return false;
  for(var i=0;i<old.length;i++){
    final a=old[i],b=next[i];
    for(final k in const ['id','kind','body','edited_at','deleted_at','url','attachment_name','transcript','sender_id']){
      if(a[k]!=b[k])return false;
    }
    final aa=a['attachments'] as List?,bb=b['attachments'] as List?;
    if((aa?.length??0)!=(bb?.length??0))return false;
    for(var j=0;j<(aa?.length??0);j++){
      final x=aa![j],y=bb![j];
      if(x is Map&&y is Map){if(x['url']!=y['url']||x['path']!=y['path'])return false;}
      else if(x!=y)return false;
    }
  }
  return true;
}
String _name(Map<String,dynamic> room){""".replace('\u00024','\u0024'), 'helpers')

replace_once("tick=Timer.periodic(const Duration(seconds:95)","tick=Timer.periodic(const Duration(seconds:120)",'room-list periodic')
replace_once("title:const Text('Чаты'),actions:","title:const Text('Чаты',style:TextStyle(fontWeight:FontWeight.w700)),actions:",'list title')
replace_once("return ListTile(leading:ListenableBuilder(listenable:AvatarStore.instance,builder:(_,__) {final avatar=_personAvatar(r);return CircleAvatar(backgroundImage:avatar,child:avatar==null?Icon(r['kind']=='saved'?Icons.bookmark_outline:r['kind']=='group'?Icons.group_outlined:Icons.person_outline):null);}),", """return ListTile(contentPadding:const EdgeInsets.fromLTRB(15,5,12,5),
           leading:ListenableBuilder(listenable:AvatarStore.instance,builder:(_,__) {final avatar=_personAvatar(r);return CircleAvatar(radius:24,backgroundImage:avatar,child:avatar==null?Icon(r['kind']=='saved'?Icons.bookmark_outline:r['kind']=='group'?Icons.group_outlined:Icons.person_outline):null);}),""",'list avatar')
replace_once("subtitle:Text(_preview(last),maxLines:1,overflow:TextOverflow.ellipsis),", "subtitle:Text(_preview(last),maxLines:1,overflow:TextOverflow.ellipsis,style:const TextStyle(fontSize:13.5,height:1.35)),",'list preview')
replace_once("   await _refresh(silent:messages.isNotEmpty);\n   if(mounted&&room==null)unawaited(_reloadRoom());", """   // The title/avatar request can run concurrently with initial message fetch.
   // Sequential cold loads previously added one server round-trip to another.
   if(room==null)unawaited(_reloadRoom());
   await _refresh(silent:messages.isNotEmpty);""",'parallel room cold start')
replace_once("tick=Timer.periodic(const Duration(seconds:35)","tick=Timer.periodic(const Duration(seconds:18)",'delta poll')
replace_once("final full=!silent||messages.isEmpty||polls%10==0;", "final full=!silent||messages.isEmpty||polls%15==0;",'bounded full resync')
replace_once("""       final oldSignature=messages.map((x)=>'4{x['id']}:4{x['body']}:4{x['edited_at']}:4{x['deleted_at']}:4{x['url']}:4{x['attachments']}').join('|');
       final newSignature=next.map((x)=>'4{x['id']}:4{x['body']}:4{x['edited_at']}:4{x['deleted_at']}:4{x['url']}:4{x['attachments']}').join('|');
       if(oldSignature!=newSignature||loading){""".replace('\u00024','\u0024'),"""       // Compare visible fields without allocating two huge joined strings.
       if(!_sameMessagePage(messages,next)||loading){""",'avoid expensive signature')

replace_once("Widget _bubble(Map<String,dynamic> m){","Widget _bubble(Map<String,dynamic> m,{bool showAvatar=true,bool showSender=true}){",'bubble parameters')
replace_once("   return Align(alignment:mine?Alignment.centerRight:Alignment.centerLeft,child:Row(mainAxisSize:MainAxisSize.min,crossAxisAlignment:CrossAxisAlignment.end,children:[", """   final colors=Theme.of(context).colorScheme;
   final maxWidth=(MediaQuery.sizeOf(context).width*.78).clamp(180.0,470.0).toDouble();
   final outgoing=colors.primaryContainer;
   final incoming=colors.surfaceContainerLow;
   return Align(alignment:mine?Alignment.centerRight:Alignment.centerLeft,child:Row(mainAxisSize:MainAxisSize.min,crossAxisAlignment:CrossAxisAlignment.end,children:[""",'bubble palette')
replace_once("if(!mine)ListenableBuilder(listenable:AvatarStore.instance,builder:(_,__){final bytes=AvatarStore.instance.bytes('4{m['sender_id']}');return Padding(padding:const EdgeInsets.only(left:5,bottom:5),child:CircleAvatar(radius:15,backgroundImage:bytes==null?null:MemoryImage(bytes),child:bytes==null?const Icon(Icons.person_outline,size:17):null));}),".replace('\u00024','\u0024'),"""if(!mine)showAvatar?ListenableBuilder(listenable:AvatarStore.instance,builder:(_,__){final bytes=AvatarStore.instance.bytes('4{m['sender_id']}');return Padding(padding:const EdgeInsets.only(left:5,bottom:4),child:CircleAvatar(radius:15,backgroundImage:bytes==null?null:MemoryImage(bytes),child:bytes==null?const Icon(Icons.person_outline,size:16):null));}):const SizedBox(width:35),""".replace('\u00024','\u0024'),'group avatars only at end')
replace_once("Flexible(child:ConstrainedBox(constraints:const BoxConstraints(maxWidth:325),child:GestureDetector(","Flexible(child:ConstrainedBox(constraints:BoxConstraints(maxWidth:maxWidth),child:GestureDetector(",'adaptive bubble width')
replace_once("""onLongPress:()=>_messageAction(m),child:Container(margin:const EdgeInsets.symmetric(horizontal:7,vertical:3),padding:const EdgeInsets.fromLTRB(11,8,11,6),
       decoration:BoxDecoration(color:mine?Theme.of(context).colorScheme.primaryContainer:Theme.of(context).colorScheme.surfaceContainerHighest,borderRadius:BorderRadius.circular(16)),""","""onLongPress:()=>_messageAction(m),child:Container(
       margin:EdgeInsets.fromLTRB(6,showSender?4:1,6,showAvatar?5:1),
       padding:const EdgeInsets.fromLTRB(13,9,12,7),
       decoration:BoxDecoration(
         color:mine?outgoing:incoming,
         border:Border.all(color:colors.outlineVariant.withValues(alpha:.21),width:.65),
         borderRadius:BorderRadius.only(
           topLeft:const Radius.circular(18),topRight:const Radius.circular(18),
           bottomLeft:Radius.circular(mine?18:5),bottomRight:Radius.circular(mine?5:18)),
         boxShadow:[BoxShadow(color:colors.shadow.withValues(alpha:.035),blurRadius:5,offset:const Offset(0,1))]),""",'modern bubble skin')
replace_once("if(room?['kind']=='group'&&!mine)Padding", "if(room?['kind']=='group'&&!mine&&showSender)Padding",'sender only first bubble')
replace_once("if(!deleted&&'4{m['body']??''}'.isNotEmpty)Text('4{m['body']}',style:const TextStyle(fontSize:15)),".replace('\u00024','\u0024'),"""if(!deleted&&'4{m['body']??''}'.isNotEmpty)Text('4{m['body']}',
           style:const TextStyle(fontSize:15.5,height:1.37,letterSpacing:.07)),""".replace('\u00024','\u0024'),'text typography')
replace_once("""         Align(alignment:Alignment.centerRight,child:Text(m['id'].toString().startsWith('local:')
           ? '4{_time(m['created_at'])} · …'
           : '4{m['edited_at']!=null?'изменено · ':''}4{_time(m['created_at'])}4{mine?(read?' ✓✓':' ✓'):''}',
           style:Theme.of(context).textTheme.labelSmall)),""".replace('\u00024','\u0024'),"""         Padding(padding:const EdgeInsets.only(top:3),child:Align(
           alignment:Alignment.centerRight,
           child:Row(mainAxisSize:MainAxisSize.min,children:[
             if(m['edited_at']!=null)Padding(padding:const EdgeInsets.only(right:5),child:Text('изменено',style:TextStyle(fontSize:10.5,color:colors.onSurfaceVariant))),
             Text(_time(m['created_at']),style:TextStyle(fontSize:10.5,fontWeight:FontWeight.w400,color:colors.onSurfaceVariant.withValues(alpha:.82))),
             if(mine)Padding(padding:const EdgeInsets.only(left:4),child:Semantics(
               label:m['id'].toString().startsWith('local:')?'Отправляется':(read?'Прочитано':'Отправлено'),
               child:Icon(m['id'].toString().startsWith('local:')?Icons.schedule_rounded:
                 (read?Icons.done_all_rounded:Icons.done_rounded),
                 size:15,color:read?colors.primary:colors.onSurfaceVariant.withValues(alpha:.72)))),
           ]))),""",'minimal receipt icons')
replace_once("""         ListView.builder(controller:list,padding:const EdgeInsets.symmetric(vertical:9),itemCount:visible.length,itemBuilder:(_,i)=>_bubble(visible[i]))),""", """         ListView.builder(controller:list,cacheExtent:420,
           padding:const EdgeInsets.symmetric(vertical:11),itemCount:visible.length,itemBuilder:(_,i){
             final current=visible[i];
             final showDate=i==0||_dayKey(current['created_at'])!=_dayKey(visible[i-1]['created_at']);
             final showAvatar=i==visible.length-1||visible[i+1]['sender_id']!=current['sender_id'];
             final showSender=i==0||visible[i-1]['sender_id']!=current['sender_id'];
             return KeyedSubtree(key:ValueKey('msg-4{current['id']}'),child:Column(children:[
               if(showDate)Padding(padding:const EdgeInsets.symmetric(vertical:11),child:DecoratedBox(
                 decoration:BoxDecoration(color:Theme.of(context).colorScheme.surfaceContainerHighest.withValues(alpha:.62),
                   borderRadius:BorderRadius.circular(11)),
                 child:Padding(padding:const EdgeInsets.symmetric(horizontal:12,vertical:5),
                   child:Text(_dayTitle(current['created_at']),style:TextStyle(fontSize:11.5,
                     fontWeight:FontWeight.w600,color:Theme.of(context).colorScheme.onSurfaceVariant))))),
               _bubble(current,showAvatar:showAvatar,showSender:showSender),
             ]));
           })),""".replace('\u00024','\u0024'),'compact grouped chat list & day headers')
replace_once("""Expanded(child:TextField(controller:text,enabled:!busy,minLines:1,maxLines:4,textCapitalization:TextCapitalization.sentences,
            onSubmitted:(_)=>_send(),decoration:InputDecoration(hintText:_draftPhotos.isEmpty?'Сообщение':'Подпись к фотографиям',isDense:true,filled:true,border:OutlineInputBorder(borderRadius:BorderRadius.circular(22),borderSide:BorderSide.none)))),""","""Expanded(child:TextField(controller:text,enabled:!busy,minLines:1,maxLines:4,
            style:const TextStyle(fontSize:15.5,height:1.32),textCapitalization:TextCapitalization.sentences,
            onSubmitted:(_)=>_send(),decoration:InputDecoration(hintText:_draftPhotos.isEmpty?'Написать сообщение…':'Подпись к фотографиям',isDense:true,filled:true,
              contentPadding:const EdgeInsets.symmetric(horizontal:17,vertical:11),
              border:OutlineInputBorder(borderRadius:BorderRadius.circular(23),borderSide:BorderSide.none)))),""",'composer')
replace_once("return IconButton(tooltip:'Отправить сообщение',onPressed:busy?null:_send,icon:const Icon(Icons.send_rounded));", "return IconButton.filled(tooltip:'Отправить сообщение',onPressed:busy?null:_send,icon:const Icon(Icons.arrow_upward_rounded,size:21));",'send button')
p.write_text(s,encoding='utf-8')

service=Path('lib/core/services/promysel_chat_service.dart')
v=service.read_text(encoding='utf-8')
old="""      for(final e in previous.entries){
        final latest=result.where((r)=>'4{r['id']}'==e.key).firstOrNull;
        if(!serverIds.contains(e.key)||
           (latest!=null&&'4{latest['visibleSince']??''}'!='4{e.value['visibleSince']??''}')){
          _evictHistory(e.key);
        }
      }
""".replace('\u00024','\u0024')
new="""      // Build an index once. Repeated linear scans slowed down room refresh
      // when many conversations were available.
      final latestById=<String,Map<String,dynamic>>{
        for(final r in result) '4{r['id']}':r,
      };
      for(final e in previous.entries){
        final latest=latestById[e.key];
        if(latest==null||'4{latest['visibleSince']??''}'!='4{e.value['visibleSince']??''}'){
          _evictHistory(e.key);
        }
      }
""".replace('\u00024','\u0024')
assert v.count(old)==1,('linear rooms scan',v.count(old))
v=v.replace(old,new,1)
assert v.count("final serverIds=result.map((r)=>'4{r['id']}').toSet();".replace('\u00024','\u0024'))==1
v=v.replace("      final serverIds=result.map((r)=>'4{r['id']}').toSet();\n".replace('\u00024','\u0024'),'',1)
service.write_text(v,encoding='utf-8')
print('PASS: chat typography, read receipts, grouped avatars, day labels, cold load, delta polling and O(n) rooms refresh')