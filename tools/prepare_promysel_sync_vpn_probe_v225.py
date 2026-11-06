#!/usr/bin/env python3
"""v2.25: compare real authenticated Supabase sync API with/without VPN.

The new diagnostic performs a bounded GET of field domain revisions. It never
sends measurements, advances the sync cursor or touches local pending queues.
"""
from pathlib import Path
p=Path('lib/features/menu/about_screen.dart')
s=p.read_text(encoding='utf-8')

def one(old,new,label):
 global s
 if s.count(old)!=1:raise AssertionError(f'{label}: anchor count {s.count(old)}')
 s=s.replace(old,new,1)

one("import 'dart:async';",
"""import 'dart:async';
import 'dart:convert';
import 'package:flutter/services.dart';
import '../../core/services/session_service.dart';""","imports")

one("  String _checkStatus='Проверка ещё не выполнялась';",
"""  String _checkStatus='Проверка ещё не выполнялась';
  bool _apiBusy=false;
  bool? _apiOk;
  int? _apiMs;
  String _apiCode='NOT_RUN', _apiDetail='Проверка не выполнялась';
  String _vpnMode='off';
  final Map<String,String> _vpnResults={};

  void _rememberApiProbe(){
    final label=_apiOk==true?'Доступен':_apiOk==false?'Ошибка':'Не проверен';
    final ms=_apiMs==null?'—':_apiMs.toString()+' мс';
    _vpnResults[_vpnMode]='${_stamp(DateTime.now())}: $label · $_apiCode · $ms · $_apiDetail';
  }

  /// Read-only probe: verifies the SAME authenticated Edge origin and DB
  /// revision-read endpoint used by actual sync. It does not prove any
  /// pending measurement was uploaded and cannot be used as an ACK.
  Future<void> _probeApi() async {
    _apiOk=null;_apiMs=null;_apiCode='NOT_RUN';
    _apiDetail='Проверяем авторизованный API синхронизации…';
    final fieldId=SessionService.instance.currentFieldId;
    final token=SessionService.instance.token;
    if(fieldId==null||fieldId.isEmpty||token==null||token.isEmpty||
       token.startsWith('offline-')){
      _apiCode='NO_SESSION';
      _apiDetail='Для теста требуется действующий вход и выбранное месторождение.';
      _rememberApiProbe();
      return;
    }
    final timer=Stopwatch()..start();
    try {
      final uri=Uri.parse('$_base/v1/sync/domain/revisions').replace(
        queryParameters:{
          'fieldId':fieldId,
          'probe':DateTime.now().millisecondsSinceEpoch.toString()
        });
      final response=await http.get(uri,headers:{
        'authorization':'Bearer $token',
        'accept':'application/json'
      }).timeout(const Duration(seconds:12));
      _apiCode='HTTP_${response.statusCode}';
      if(response.statusCode==200){
        final json=jsonDecode(response.body);
        if(json is Map&&json['revisions'] is Map){
          _apiOk=true;
          _apiDetail='Сервер и чтение ревизий синхронизации доступны.';
        }else{
          _apiOk=false;_apiCode='INVALID_SYNC_RESPONSE';
          _apiDetail='Ответ получен, но формат ревизий неправильный.';
        }
      }else{
        _apiOk=false;
        _apiDetail=response.statusCode==401
          ?'Сервер отвечает, но авторизация отклонена (401).'
          :response.statusCode==403
          ?'Сервер отвечает, но доступ к месторождению запрещён (403).'
          :response.statusCode==409
          ?'Сервер отвечает, но произошёл конфликт данных (409).'
          :response.statusCode>=500
          ?'Сервер отвечает с внутренней ошибкой.'
          :'Сервер ответил с кодом ${response.statusCode}.';
      }
    } on TimeoutException {
      _apiOk=false;_apiCode='SYNC_API_TIMEOUT';
      _apiDetail='Не получен ответ за 12 секунд.';
    } on http.ClientException {
      _apiOk=false;_apiCode='SYNC_API_NETWORK';
      _apiDetail='Сбой подключения: DNS / TLS / маршрут / сеть.';
    } on FormatException {
      _apiOk=false;_apiCode='SYNC_API_INVALID_JSON';
      _apiDetail='API ответил, но JSON не читается.';
    } catch (_) {
      _apiOk=false;_apiCode='SYNC_API_CLIENT';
      _apiDetail='Невозможно выполнить проверку API.';
    } finally {
      timer.stop();_apiMs=timer.elapsedMilliseconds;
      _rememberApiProbe();
    }
  }

  Future<void> _checkApiOnly() async {
    if(_checking||_apiBusy)return;
    setState(()=>_apiBusy=true);
    try{await _probeApi();}
    finally{if(mounted)setState(()=>_apiBusy=false);}
  }

  Future<void> _copyVpnResults() async {
    final report=<String>[
      'Промысел — диагностический GET API синхронизации',
      'VPN задаётся пользователем вручную, браузер его не определяет.',
      "Без VPN: ${_vpnResults['off']??'Не проверено'}",
      "С VPN: ${_vpnResults['on']??'Не проверено'}",
      'GET /v1/sync/domain/revisions: только чтение',
      'Успешный GET не доказывает отправку замеров.',
      'Без токенов, ФИО, скважин и значений параметров.'
    ].join(String.fromCharCode(10));
    await Clipboard.setData(ClipboardData(text:report));
    if(mounted)ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content:Text('Результаты проверки скопированы')));
  }
""","state and read-only probe")
one("    if(_checking||sync.syncing)return;",
    "    if(_checking||sync.syncing||_apiBusy)return;",
    "no simultaneous full/diagnostic check")
one("      _systemOk=null;_serverOk=null;_syncOk=null;",
    "      _systemOk=null;_serverOk=null;_syncOk=null;\n      _apiOk=null;_apiMs=null;_apiCode='NOT_RUN';",
    "reset API check")
one("      // Health must NOT gate a real HTTPS sync, especially on mobile handover.",
"""      // Check an authenticated DB read independently of public /health.
      // Only the existing explicit full check may send queued changes.
      await _probeApi();
      if(_apiOk==false)_issues.add(_CheckIssue(
        _apiDetail,_apiCode,'Проверка API синхронизации',
        stage:'sync.domain.revisions'));
      // Health must NOT gate a real HTTPS sync, especially on mobile handover.""",
    "new check in existing full diagnostic")
one("        final disabled=_checking||sync.syncing;",
    "        final disabled=_checking||sync.syncing||_apiBusy;",
    "disable while probing")
one("""              _line(Icons.sync,'Синхронизация',_syncOk,
                pending:_checking?'Проверяется':'Не проверено'),""",
"""              _line(Icons.sync,'Синхронизация',_syncOk,
                pending:_checking?'Проверяется':'Не проверено'),
              _line(Icons.lan_outlined,'API синхронизации (чтение)',_apiOk,
                pending:(_checking||_apiBusy)?'Проверяется':
                  _apiCode=='NO_SESSION'?'Нужен вход':'Не проверено'),
              Text("Время API: ${_apiMs==null?'—':'$_apiMs мс'}"
                ' · Код: $_apiCode',style:TextStyle(fontSize:13,
                  color:scheme.onSurfaceVariant)),
              Text(_apiDetail,style:TextStyle(fontSize:13,
                  color:scheme.onSurfaceVariant)),
              const SizedBox(height:12),
              const Text('Для сравнения VPN укажите его реальное состояние '
                'на телефоне. Эта отдельная проверка не отправляет замеры.',
                style:TextStyle(fontSize:13)),
              Row(children:[
                const Text('VPN: '),
                Expanded(child:DropdownButton<String>(
                  isExpanded:true,value:_vpnMode,
                  onChanged:disabled?null:(mode){
                    if(mode!=null)setState(()=>_vpnMode=mode);
                  },
                  items:const [
                    DropdownMenuItem(value:'off',child:Text('Выключен')),
                    DropdownMenuItem(value:'on',child:Text('Включён')),
                  ])),
              ]),
              TextButton.icon(
                onPressed:disabled?null:_checkApiOnly,
                icon:const Icon(Icons.wifi_find),
                label:Text(_apiBusy?'Проверяем API…':
                  'Проверить только API (без отправки)')),
              if(_vpnResults.isNotEmpty)...[
                const SizedBox(height:5),
                Text("Без VPN: ${_vpnResults['off']??'Не проверено'}",
                  style:const TextStyle(fontSize:13)),
                const SizedBox(height:4),
                Text("С VPN: ${_vpnResults['on']??'Не проверено'}",
                  style:const TextStyle(fontSize:13)),
                TextButton.icon(
                  onPressed:_copyVpnResults,
                  icon:const Icon(Icons.copy_outlined),
                  label:const Text('Скопировать сравнение')),
              ],""",
    "API indicator and on/off comparison in connection card")
assert s.count("FilledButton.icon(")==1
assert "OutlinedButton.icon(" not in s
assert s.count("Версия v2.24")==2
s=s.replace("Версия v2.24","Версия v2.25")
p.write_text(s,encoding='utf-8')
print('PASS v2.25: VPN comparison, authorized API GET 12s, latency/status, no queue mutation')
