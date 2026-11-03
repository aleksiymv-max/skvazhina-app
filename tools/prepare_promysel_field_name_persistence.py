"""Keep authoritative field names in local cache and refresh them on session restore."""
from pathlib import Path
r=Path.cwd()
p=r/'lib/core/services/session_service.dart'
s=p.read_text(encoding='utf-8')
old=" Future<void> refreshFields()async{final d=await RegistrationService.instance.fields();final raw=d['items'];fields.clear();if(raw is List){for(final x in raw){if(x is Map){final m=Map<String,dynamic>.from(x);final id=(m['id']??m['fieldId']??m['field_id']??'').toString();final name=(m['name']??m['fieldName']??m['field_name']??'').toString();if(id.isNotEmpty&&name.isNotEmpty)fields.add(OilFieldRegistration(id:id,name:name,approved:true));}}}notifyListeners();}"
assert s.count(old)==1
s=s.replace(old,""" Future<void> refreshFields()async{
   final d=await RegistrationService.instance.fields();
   final raw=d['items'];
   if(raw is! List)throw const FormatException('Сервер не вернул список месторождений');
   final loaded=<OilFieldRegistration>[];
   for(final x in raw){
     if(x is! Map)continue;
     final m=Map<String,dynamic>.from(x);
     final id=(m['id']??m['fieldId']??m['field_id']??'').toString();
     final name=(m['name']??m['fieldName']??m['field_name']??'').toString().trim();
     if(id.isNotEmpty&&name.isNotEmpty&&!name.startsWith('field-')){
       loaded.add(OilFieldRegistration(id:id,name:name,approved:true));
       _fieldNameCache[id]=name;
     }
   }
   // An empty/partial response must not erase a previously verified field name.
   if(loaded.isNotEmpty){
     fields..clear()..addAll(loaded);
     await (await SharedPreferences.getInstance()).setString('promysel_field_names_v1',jsonEncode(_fieldNameCache));
   }
   notifyListeners();
 }
 Future<void> restoreFieldNames()async{
   final prefs=await SharedPreferences.getInstance();
   try{
     final raw=prefs.getString('promysel_field_names_v1');
     if(raw!=null){
       final decoded=jsonDecode(raw);
       if(decoded is Map)for(final e in decoded.entries){
         final id=e.key.toString(),name=e.value.toString().trim();
         if(id.isNotEmpty&&name.isNotEmpty&&!name.startsWith('field-'))_fieldNameCache[id]=name;
       }
     }
   }catch(_){/* Corrupted cache must not prevent login */ }
   notifyListeners();
 }
""",1)
old="final prefs=await SharedPreferences.getInstance();final raw=prefs.getString(_sessionKey);"
assert s.count(old)==1
s=s.replace(old,"final prefs=await SharedPreferences.getInstance();await restoreFieldNames();final raw=prefs.getString(_sessionKey);",1)
old="try{await ensureFreshToken();}catch(_){/* can still work offline */}notifyListeners();return true;"
assert s.count(old)==1
s=s.replace(old,"try{await ensureFreshToken();}catch(_){/* can still work offline */}unawaited(refreshFields().catchError((_){ }));notifyListeners();return true;",1)
old="return 'Месторождение';}"
assert s.count(old)==1
s=s.replace(old,"return 'Загрузка месторождения…';}",1)
p.write_text(s,encoding='utf-8')
prof=r/'lib/features/organization/profile_screen.dart'
s=prof.read_text(encoding='utf-8')
old="@override Widget build(BuildContext context){final u=SessionService.instance.currentUser;"
assert s.count(old)==1
s=s.replace(old,"@override Widget build(BuildContext context)=>ListenableBuilder(listenable:SessionService.instance,builder:(context,_){final u=SessionService.instance.currentUser;",1)
old="icon:const Icon(Icons.logout),label:const Text('Выйти из приложения'))]));}"
assert s.count(old)==1
s=s.replace(old,"icon:const Icon(Icons.logout),label:const Text('Выйти из приложения'))]));});",1)
prof.write_text(s,encoding='utf-8')
assert 'promysel_field_names_v1' in p.read_text() and 'unawaited(refreshFields()' in p.read_text()
assert 'ListenableBuilder(listenable:SessionService.instance' in prof.read_text()
print('PASS: verified field names cached, refreshed and profile reactive')
