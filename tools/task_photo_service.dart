import 'dart:convert';
import 'dart:math';
import 'dart:typed_data';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart';
import 'package:image_picker/image_picker.dart';
import '../models/work_task.dart';
import 'session_service.dart';

class TaskSelectedPhoto {
  TaskSelectedPhoto(this.id,this.bytes,this.name,this.mime);
  final String id,name,mime;
  final Uint8List bytes;
}
class TaskPhotoSelectionController extends ChangeNotifier {
  final List<TaskSelectedPhoto> photos=[];
  final ImagePicker picker=ImagePicker();
  bool picking=false;
  String? error;
  static final Random random=Random.secure();
  static String newId(){
    final b=List<int>.generate(16,(_)=>random.nextInt(256));
    b[6]=(b[6]&0x0f)|0x40;b[8]=(b[8]&0x3f)|0x80;
    final s=b.map((x)=>x.toRadixString(16).padLeft(2,'0')).join();
    return s.substring(0,8)+'-'+s.substring(8,12)+'-'+s.substring(12,16)+'-'+s.substring(16,20)+'-'+s.substring(20);
  }
  Future<void> pick(ImageSource source)async{
    if(picking)return;
    picking=true;error=null;notifyListeners();
    try{
      final List<XFile> selected=[];
      if(source==ImageSource.camera){
        final item=await picker.pickImage(source:source,maxWidth:1600,imageQuality:75);
        if(item!=null)selected.add(item);
      }else{
        selected.addAll(await picker.pickMultiImage(maxWidth:1600,imageQuality:75));
      }
      for(final item in selected){
        if(photos.length>=5){error='Не более 5 фотографий за одно действие';break;}
        final bytes=await item.readAsBytes();
        if(bytes.isEmpty||bytes.length>5242880){error='Фотография должна быть меньше 5 МБ';continue;}
        final name=item.name.toLowerCase();
        final mime=name.endsWith('.png')?'image/png':name.endsWith('.webp')?'image/webp':
          name.endsWith('.jpg')||name.endsWith('.jpeg')?'image/jpeg':null;
        if(mime==null){error='Поддерживаются JPEG, PNG и WebP';continue;}
        photos.add(TaskSelectedPhoto(newId(),bytes,item.name,mime));
      }
    }catch(e){error='Не удалось выбрать фотографию: '+e.toString();}
    finally{picking=false;notifyListeners();}
  }
  void remove(String id){photos.removeWhere((x)=>x.id==id);notifyListeners();}
}
class TaskPhotoService {
  TaskPhotoService._();
  static final instance=TaskPhotoService._();
  static const base='https://xptmcufhuvtcunqzlsme.supabase.co/functions/v1/promysel-task-photos';
  // Read-only metadata for a task is cached briefly, per field AND user.
  // No photos are cached in this map; signed originals load on explicit tap.
  final Map<String,List<Map<String,dynamic>>> _listCache={};
  final Map<String,DateTime> _listCachedAt={};
  final Map<String,Future<List<Map<String,dynamic>>>> _listPending={};
  String _key(String field,String task)=>SessionService.instance.currentUser.id+
    '|'+field+'|'+task;
  void _invalidate(String field,String task){
    final k=_key(field,task);
    _listCache.remove(k);
    _listCachedAt.remove(k);
  }
  Future<String> token()async{
    await SessionService.instance.ensureFreshToken();
    final t=SessionService.instance.token;
    if(t==null||t.isEmpty)throw Exception('Войдите в приложение');
    return t;
  }
  Map<String,dynamic> parse(http.Response res){
    dynamic raw;
    try{raw=jsonDecode(utf8.decode(res.bodyBytes));}catch(_){throw Exception('Некорректный ответ сервера фотографий');}
    final d=raw is Map?Map<String,dynamic>.from(raw):<String,dynamic>{};
    if(res.statusCode<200||res.statusCode>=300)throw Exception((d['detail']??'Ошибка сервера: '+res.statusCode.toString()).toString());
    return d;
  }
  Future<void> register(WorkTask task)async{
    final fieldId=SessionService.instance.currentFieldId;
    if(fieldId==null||fieldId.isEmpty)throw Exception('Месторождение не выбрано');
    final t=await token();
    final res=await http.post(Uri.parse(base+'/register'),headers:{
      'authorization':'Bearer '+t,'content-type':'application/json'},
      body:jsonEncode({'fieldId':fieldId,'taskId':task.id,
        'targetType':task.targetType.name,'targetId':task.targetId})
    ).timeout(const Duration(seconds:16));
    parse(res);
    _invalidate(fieldId,task.id);
  }
  Future<void> upload(WorkTask task,String phase,List<TaskSelectedPhoto> photos)async{
    if(photos.isEmpty)return;
    final fieldId=SessionService.instance.currentFieldId;
    if(fieldId==null||fieldId.isEmpty)throw Exception('Месторождение не выбрано');
    for(final photo in photos){
      final req=http.MultipartRequest('POST',Uri.parse(base+'/upload'));
      req.headers['authorization']='Bearer '+await token();
      req.fields.addAll({'fieldId':fieldId,'taskId':task.id,'phase':phase,'clientId':photo.id});
      req.files.add(http.MultipartFile.fromBytes('photo',photo.bytes,
        filename:photo.name,contentType:MediaType.parse(photo.mime)));
      final stream=await req.send().timeout(const Duration(seconds:35));
      parse(await http.Response.fromStream(stream));
      // If a later upload fails, already confirmed images remain visible
      // rather than being hidden behind a cached empty list.
      _invalidate(fieldId,task.id);
    }
  }
  Future<List<Map<String,dynamic>>> list(WorkTask task,{bool force=false})async{
    final fieldId=SessionService.instance.currentFieldId;
    if(fieldId==null)return [];
    final key=_key(fieldId,task.id);
    final cachedAt=_listCachedAt[key];
    if(!force&&cachedAt!=null&&_listCache.containsKey(key)&&
       DateTime.now().difference(cachedAt)<const Duration(seconds:20)){
      return _listCache[key]!.map((r)=>Map<String,dynamic>.from(r)).toList();
    }
    if(_listPending.containsKey(key))return _listPending[key]!;
    Future<List<Map<String,dynamic>>> load()async{
      final uri=Uri.parse(base+'/list').replace(
        queryParameters:{'fieldId':fieldId,'taskId':task.id});
      final res=await http.get(uri,
        headers:{'authorization':'Bearer '+await token()})
        .timeout(const Duration(seconds:14));
      final items=parse(res)['items'];
      final rows=items is List?items.whereType<Map>()
        .map((x)=>Map<String,dynamic>.from(x)).toList():<Map<String,dynamic>>[];
      if(_listCache.length>=64){
        final oldest=_listCache.keys.first;
        _listCache.remove(oldest);
        _listCachedAt.remove(oldest);
      }
      _listCache[key]=rows;
      _listCachedAt[key]=DateTime.now();
      return rows.map((r)=>Map<String,dynamic>.from(r)).toList();
    }
    final pending=load();
    _listPending[key]=pending;
    try{return await pending;}finally{_listPending.remove(key);}
  }
  Future<String> signedUrl(String photoId)async{
    final res=await http.get(Uri.parse(base+'/'+photoId+'/url'),
      headers:{'authorization':'Bearer '+await token()}).timeout(const Duration(seconds:14));
    return (parse(res)['url']??'').toString();
  }
}
