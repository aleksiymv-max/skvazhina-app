import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'dart:convert';
import 'dart:typed_data';
import 'package:http/http.dart' as http;
import 'package:image_picker/image_picker.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../network/api_config.dart';
import 'session_service.dart';

/// All requests are authorized by Supabase Auth and verified again on the server.
/// No service-role key or raw chat tables are exposed to the Flutter client.
class PromyselChatService {
  PromyselChatService._();
  static final instance=PromyselChatService._();
  final String baseUrl=ApiConfig.baseUrl.replaceFirst(RegExp(r'promysel-compat/?$'),'promysel-chat');
  String get userId=>SessionService.instance.currentUser.id;
  String get fieldId=>SessionService.instance.currentFieldId??'';
  Future<Map<String,dynamic>> call(String method,String path,{Map<String,dynamic>? data,Map<String,String>? query})async{
    await SessionService.instance.ensureFreshToken();
    final token=SessionService.instance.api.token;
    if(token==null||token.isEmpty)throw Exception('Требуется вход в приложение');
    final u=Uri.parse('$baseUrl$path').replace(queryParameters:query);
    final req=http.Request(method,u);
    req.headers.addAll({'Authorization':'Bearer $token','Content-Type':'application/json'});
    if(data!=null)req.body=jsonEncode(data);
    final streamed=await req.send().timeout(const Duration(seconds:18));
    final res=await http.Response.fromStream(streamed).timeout(const Duration(seconds:18));
    Map<String,dynamic> result;
    try{result=Map<String,dynamic>.from(jsonDecode(res.body) as Map);}catch(_){throw Exception('Некорректный ответ сервера чатов');}
    if(res.statusCode<200||res.statusCode>=300)throw Exception((result['detail']??'Ошибка чата ${res.statusCode}').toString());
    return result;
  }
  List<Map<String,dynamic>> _list(Map<String,dynamic> r)=>((r['items'] as List?)??[]).whereType<Map>().map((e)=>Map<String,dynamic>.from(e)).toList();
  Future<List<Map<String,dynamic>>> rooms()=>call('GET','/rooms',query:{'fieldId':fieldId}).then(_list);
  Future<List<Map<String,dynamic>>> users()=>call('GET','/users',query:{'fieldId':fieldId}).then(_list);
  Future<List<Map<String,dynamic>>> messages(String id,{DateTime? before})=>call('GET','/rooms/$id/messages',query:before==null?null:{'before':before.toUtc().toIso8601String()}).then(_list);
  Future<String> create(String kind,{required List<String> people,String title=''})async{
    final r=await call('POST','/rooms',data:{'fieldId':fieldId,'kind':kind,'title':title,'people':people});
    return r['id'].toString();
  }
  Future<void> sendText(String room,String text)async{
    if(text.trim().isEmpty)return;
    await call('POST','/rooms/$room/messages',data:{'kind':'text','body':text.trim()});
  }
  Future<String> upload(String room,XFile file,String kind)async{
    final size=await file.length();
    if(size<=0||size>50*1024*1024)throw Exception('Размер вложения должен быть до 50 МБ');
    final name=file.name.isEmpty?'attachment':file.name;
    final mime=_mime(name,kind);
    final result=await call('POST','/rooms/$room/upload',data:{'name':name,'size':size,'mimeType':mime,'kind':kind});
    final url=(result['uploadUrl']??'').toString();
    if(url.isEmpty)throw Exception('Не удалось получить адрес загрузки');
    final bytes=await file.readAsBytes();
    final upload=await http.put(Uri.parse(url),headers:{'Content-Type':mime,'x-upsert':'false'},body:bytes).timeout(const Duration(minutes:3));
    if(upload.statusCode<200||upload.statusCode>=300)throw Exception('Не удалось загрузить вложение (${upload.statusCode})');
    return '${result['path']}';
  }
  Future<void> sendMedia(String room,XFile file,String kind,{String caption=''})async{
    final path=await upload(room,file,kind);
    await call('POST','/rooms/$room/messages',data:{'kind':kind,'body':caption,'path':path,
      'name':file.name,'mimeType':_mime(file.name,kind),'size':await file.length()});
  }
  Future<void> groupAvatar(String room,XFile file)async{
    final path=await upload(room,file,'image');
    await call('PATCH','/rooms/$room/settings',data:{'avatarPath':path});
  }
  String _mime(String file,String kind){
    final n=file.toLowerCase();
    if(kind=='voice')return n.endsWith('.webm')?'audio/webm':n.endsWith('.ogg')?'audio/ogg':'audio/mp4';
    if(kind=='video')return n.endsWith('.mov')?'video/quicktime':n.endsWith('.webm')?'video/webm':'video/mp4';
    if(kind=='image')return n.endsWith('.png')?'image/png':n.endsWith('.webp')?'image/webp':'image/jpeg';
    if(n.endsWith('.pdf'))return 'application/pdf';
    if(n.endsWith('.txt'))return 'text/plain';
    if(n.endsWith('.docx'))return 'application/vnd.openxmlformats-officedocument.wordprocessingml.document';
    if(n.endsWith('.xlsx'))return 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';
    return 'application/octet-stream';
  }
  Future<void> settings(String room,{bool? muted,bool? soundEnabled,bool read=false,String? title})async{
    await call('PATCH','/rooms/$room/settings',data:{if(muted!=null)'muted':muted,if(soundEnabled!=null)'soundEnabled':soundEnabled,
      if(read)'read':true,if(title!=null)'title':title});
  }
  Future<void> changeMessage(String room,String id,String text)=>call('PATCH','/rooms/$room/messages/$id',data:{'body':text}).then((_){ });
  Future<void> deleteMessage(String room,String id)=>call('DELETE','/rooms/$room/messages/$id').then((_){ });
  Future<void> member(String room,String id,{required bool add})=>call(add?'POST':'DELETE','/rooms/$room/members',data:{'userId':id}).then((_){ });
  Future<void> leave(String room)=>call('POST','/rooms/$room/leave').then((_){ });
  Future<bool> soundEnabled()async{final prefs=await SharedPreferences.getInstance();return prefs.getBool('promysel_chat_sound_$userId')??true;}
  Future<void> setSound(bool on)async{final prefs=await SharedPreferences.getInstance();await prefs.setBool('promysel_chat_sound_$userId',on);}
}

/// Foreground unread badge and optional sound. OS push is a separate integration.
class PromyselChatUnread extends ValueNotifier<int>{
 PromyselChatUnread._():super(0);
 static final instance=PromyselChatUnread._();
 Timer? _timer;String _user='';bool _initialized=false,_fetching=false;
 void start(){if(_timer!=null)return;_update();_timer=Timer.periodic(const Duration(seconds:18),(_)=>_update());}
 Future<void> _update()async{
   if(_fetching)return;
   final me=SessionService.instance.currentUser.id;
   if(me.isEmpty||PromyselChatService.instance.fieldId.isEmpty){_user='';_initialized=false;if(value!=0)value=0;return;}
   if(_user!=me){_user=me;_initialized=false;value=0;}
   _fetching=true;
   try{
     final rooms=await PromyselChatService.instance.rooms();
     if(SessionService.instance.currentUser.id!=me)return;
     final total=rooms.where((r)=>r['muted']!=true).fold<int>(0,(sum,r)=>sum+((r['unread'] as num?)?.toInt()??0));
     if(_initialized&&total>value&&await PromyselChatService.instance.soundEnabled()){
       SystemSound.play(SystemSoundType.alert);
     }
     _initialized=true;if(total!=value)value=total;
   }catch(_){/* Preserve the prior badge when offline. */}
   finally{_fetching=false;}
 }
 Future<void> refresh()=>_update();
 void stop(){_timer?.cancel();_timer=null;_initialized=false;_user='';value=0;}
}