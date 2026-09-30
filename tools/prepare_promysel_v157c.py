from pathlib import Path
r=Path.cwd()
p=r/'lib/core/services/registration_service.dart'
p.write_text("""import 'dart:convert';
import 'package:http/http.dart' as http;
class RegistrationService {
 RegistrationService._(); static final instance=RegistrationService._();
 static const base=String.fromEnvironment('PROMYSEL_SYNC_URL',defaultValue:'');
 Uri u(String p){if(base.isEmpty)throw Exception('Сервер регистрации не настроен');return Uri.parse(base+(base.endsWith('/')?'':'/')+p.substring(1));}
 Map<String,dynamic> body(http.Response r){final x=jsonDecode(r.body);if(r.statusCode<200||r.statusCode>=300)throw Exception(x is Map?(x['detail']??'Ошибка сервера').toString():'Ошибка сервера');return Map<String,dynamic>.from(x as Map);}
 Future<Map<String,dynamic>> fields()async=>body(await http.get(u('/v1/registration/fields')).timeout(const Duration(seconds:12)));\n Future<Map<String,dynamic>> register(Map<String,dynamic> data)async=>body(await http.post(u('/v1/registration/apply'),headers:{'content-type':'application/json'},body:jsonEncode(data)).timeout(const Duration(seconds:12)));
 Future<Map<String,dynamic>> login(String login,String password)async=>body(await http.post(u('/v1/auth/login'),headers:{'content-type':'application/json'},body:jsonEncode({'login':login,'password':password})).timeout(const Duration(seconds:12)));
 Future<Map<String,dynamic>> pending(String token)async=>body(await http.get(u('/v1/registration/pending'),headers:{'authorization':'Bearer '+token}).timeout(const Duration(seconds:12)));
 Future<Map<String,dynamic>> approve(String token,String id,Map<String,dynamic> data)async=>body(await http.post(u('/v1/registration/'+id+'/approve'),headers:{'authorization':'Bearer '+token,'content-type':'application/json'},body:jsonEncode(data)).timeout(const Duration(seconds:12)));
 Future<Map<String,dynamic>> reject(String token,String id)async=>body(await http.post(u('/v1/registration/'+id+'/reject'),headers:{'authorization':'Bearer '+token}).timeout(const Duration(seconds:12)));\n Future<Map<String,dynamic>> firstPassword(String token,String password)async=>body(await http.post(u('/v1/auth/first-password'),headers:{'authorization':'Bearer '+token,'content-type':'application/json'},body:jsonEncode({'password':password})).timeout(const Duration(seconds:12)));
}
""")
s=p.read_text()
assert all(x in s for x in ['/v1/registration/fields','/v1/registration/apply','/v1/registration/pending','/v1/auth/login','/approve','/reject','/v1/auth/first-password'])
print('v1.57c registration transport passed')
