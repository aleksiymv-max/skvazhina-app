import 'dart:async';
import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'foreground_work_gate.dart';
import 'session_service.dart';

class PromyselNotice {
  const PromyselNotice({required this.id,required this.category,
    required this.title,required this.body,required this.route,
    required this.createdAt,required this.read});
  final int id;final String category,title,body,route;
  final DateTime createdAt;final bool read;
  factory PromyselNotice.fromJson(Map<String,dynamic> m){
    final raw=(m['route']??'/menu').toString();
    final route=RegExp(r'^/(tasks|chat/[0-9a-f-]{36}|menu|profile|wells|history)(?:$|[?])',
      caseSensitive:false).hasMatch(raw)?raw:'/menu';
    return PromyselNotice(
      id:(m['id'] as num).toInt(),category:(m['category']??'task').toString(),
      title:(m['title']??'Уведомление').toString(),body:(m['body']??'').toString(),
      route:route,createdAt:DateTime.tryParse((m['created_at']??'').toString())
        ?.toLocal()??DateTime.now(),read:m['read_at']!=null);
  }
}

/// One user+field-specific feed; server derives user identity from Auth JWT.
class PromyselNotificationHub extends ChangeNotifier {
  PromyselNotificationHub._();
  static final instance=PromyselNotificationHub._();
  static const _base='https://xptmcufhuvtcunqzlsme.supabase.co/functions/v1/promysel-device-push';
  final http.Client _client=http.Client();
  Timer? _poll,_toastTimer;
  bool _started=false,_inFlight=false,_hasBaseline=false;
  String _scope='';
  DateTime? _lastPoll;
  final List<PromyselNotice> _items=[];
  PromyselNotice? _toast;
  String? error;
  List<PromyselNotice> get items=>List.unmodifiable(_items);
  int get unread=>_items.where((e)=>!e.read).length;
  PromyselNotice? get toast=>_toast;
  String get _nowScope{
    final s=SessionService.instance;
    if(!s.currentUser.approved||s.currentUser.id.isEmpty||
       s.currentFieldId==null||s.api.token==null)return '';
    return s.currentUser.id+':'+s.currentFieldId!;
  }
  void start(){
    if(_started)return;
    _started=true;
    SessionService.instance.addListener(_userChanged);
    ForegroundWorkGate.instance.addListener(_foregroundChanged);
    _poll=Timer.periodic(const Duration(seconds:12),(_){
      if(ForegroundWorkGate.instance.isForeground)unawaited(refresh());
    });
    unawaited(refresh());
  }
  void _foregroundChanged(){
    if(ForegroundWorkGate.instance.isForeground)unawaited(refresh(force:true));
    else dismissToast();
  }
  void _userChanged(){
    final scope=_nowScope;
    if(scope!=_scope){
      _scope=scope;_items.clear();_hasBaseline=false;_lastPoll=null;error=null;
      _toastTimer?.cancel();_toast=null;notifyListeners();
      if(scope.isNotEmpty&&ForegroundWorkGate.instance.isForeground)
        unawaited(refresh(force:true));
    }
  }
  Future<void> refresh({bool force=false})async{
    if(!ForegroundWorkGate.instance.isForeground||_inFlight)return;
    final scope=_nowScope;
    if(scope.isEmpty){if(_scope.isNotEmpty)_userChanged();return;}
    if(scope!=_scope)_userChanged();
    if(!force&&_lastPoll!=null&&DateTime.now().difference(_lastPoll!)<
      const Duration(seconds:10))return;
    _lastPoll=DateTime.now();_inFlight=true;
    try{
      final session=SessionService.instance;
      await session.ensureFreshToken();
      if(scope!=_nowScope)return;
      final token=session.api.token;
      if(token==null||token.isEmpty)return;
      final url=Uri.parse('$_base/inbox').replace(
        queryParameters:{'fieldId':session.currentFieldId!});
      final res=await _client.get(url,headers:{'authorization':'Bearer $token'})
        .timeout(const Duration(seconds:10));
      if(res.statusCode!=200)throw StateError('HTTP '+res.statusCode.toString());
      final data=jsonDecode(res.body);
      if(data is! Map||data['items'] is! List)throw const FormatException('Неверный ответ');
      if(scope!=_nowScope)return;
      final next=(data['items'] as List).whereType<Map>()
        .map((e)=>PromyselNotice.fromJson(Map<String,dynamic>.from(e))).toList();
      final oldIds=_items.map((n)=>n.id).toSet();
      final baseline=!_hasBaseline;_hasBaseline=true;
      _items..clear()..addAll(next);
      error=null;
      if(!baseline)for(final n in next){
        if(!n.read&&!oldIds.contains(n.id)&&
          DateTime.now().difference(n.createdAt)<const Duration(seconds:65)){
          _showToast(n);break;
        }
      }
      notifyListeners();
    }catch(_){
      if(scope==_nowScope){error='Не удалось обновить уведомления';notifyListeners();}
    }finally{_inFlight=false;}
  }
  void _showToast(PromyselNotice notice){
    _toast=notice;_toastTimer?.cancel();
    _toastTimer=Timer(const Duration(seconds:6),dismissToast);
    notifyListeners();
  }
  void dismissToast(){
    _toastTimer?.cancel();_toastTimer=null;
    if(_toast!=null){_toast=null;notifyListeners();}
  }
  Future<void> markRead(PromyselNotice notice)async{
    final scope=_nowScope;
    if(scope.isEmpty||scope!=_scope)return;
    final i=_items.indexWhere((e)=>e.id==notice.id);
    if(i<0)return;
    final before=_items[i];
    _items[i]=PromyselNotice(id:before.id,category:before.category,
      title:before.title,body:before.body,route:before.route,
      createdAt:before.createdAt,read:true);
    if(_toast?.id==notice.id)dismissToast();
    notifyListeners();
    try{
      final s=SessionService.instance;
      await s.ensureFreshToken();
      if(scope!=_nowScope)return;
      final res=await _client.post(Uri.parse('$_base/read'),
        headers:{'authorization':'Bearer '+(s.api.token??''),
          'content-type':'application/json'},
        body:jsonEncode({'fieldId':s.currentFieldId,'id':notice.id}))
        .timeout(const Duration(seconds:10));
      if(res.statusCode!=200)throw StateError('Не сохранено');
    }catch(_){
      if(scope==_nowScope){
        final index=_items.indexWhere((n)=>n.id==notice.id);
        if(index>=0)_items[index]=before;
        notifyListeners();
      }
    }
  }
  @override void dispose(){
    _poll?.cancel();_toastTimer?.cancel();
    SessionService.instance.removeListener(_userChanged);
    ForegroundWorkGate.instance.removeListener(_foregroundChanged);
    _client.close();super.dispose();
  }
}
