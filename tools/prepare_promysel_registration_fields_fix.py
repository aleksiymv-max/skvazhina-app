#!/usr/bin/env python3
"""Fix registration on a fresh device: field list arrives asynchronously.

Run after all normal Promysel source patches. Production data, approval rules
and Supabase tables are deliberately not changed.
"""
from pathlib import Path

p=Path('lib/features/auth/login_screen.dart')
s=p.read_text(encoding='utf-8')
old=" @override void initState(){super.initState();SessionService.instance.refreshFields().catchError((_){ });}"
assert s.count(old)==1, "login initState anchor changed"
new=""" bool _fieldsLoading=false;
 String? _fieldLoadError;
 bool _fieldManuallyChosen=false;
 @override void initState(){
   super.initState();
   SessionService.instance.addListener(_onFieldsUpdated);
   _fetchFields();
 }
 void _onFieldsUpdated(){
   if(!mounted)return;
   final options=SessionService.instance.approvedFields;
   // On a fresh device the previous placeholder was 'new'. Select the actual
   // existing field once loaded, unless the user expressly chose another one.
   setState((){
     if(!_fieldManuallyChosen&&options.isNotEmpty&&
        !options.any((f)=>f.id==fieldId)){
       fieldId=options.first.id;
     }
   });
 }
 Future<void> _fetchFields()async{
   if(_fieldsLoading)return;
   setState((){_fieldsLoading=true;_fieldLoadError=null;});
   try{
     await SessionService.instance.refreshFields().timeout(const Duration(seconds:16));
     if(!mounted)return;
     final options=SessionService.instance.approvedFields;
     setState((){
       if(!_fieldManuallyChosen&&options.isNotEmpty&&
          !options.any((f)=>f.id==fieldId)){
         fieldId=options.first.id;
       }
       if(options.isEmpty)_fieldLoadError='На сервере не найдено доступных месторождений.';
     });
   }catch(_){
     if(mounted)setState(()=>_fieldLoadError=
       'Не удалось загрузить месторождения. Проверьте интернет и повторите.');
   }finally{
     if(mounted)setState(()=>_fieldsLoading=false);
   }
 }
"""
s=s.replace(old,new,1)
# Asynchronous field discovery requires a nullable selection. Otherwise
# the default value "new" can be absent from the dropdown for an operator.
old="initialValue:fieldId,decoration:const InputDecoration(labelText:'Месторождение')"
new="""initialValue:fields.any((f)=>f.id==fieldId)||
      (role==UserRole.shopChief&&fieldId=='new')?fieldId:null,
      decoration:const InputDecoration(labelText:'Месторождение',
        helperText:'Выберите существующее месторождение')"""
assert s.count(old)==1, "field picker anchor changed"
s=s.replace(old,new,1)
old="onChanged:(v)=>setState(()=>fieldId=v??'new')"
new="onChanged:(v)=>setState((){fieldId=v??'';_fieldManuallyChosen=v!=null;})"
assert s.count(old)==1, "field picker onChanged anchor changed"
s=s.replace(old,new,1)
old="const SizedBox(height:10),DropdownButtonFormField<String>(initialValue:fields.any("
new="""if(_fieldsLoading)const Padding(padding:EdgeInsets.only(top:10),
      child:LinearProgressIndicator(minHeight:2)),
    if(_fieldLoadError!=null)Padding(padding:const EdgeInsets.only(top:8),
      child:Row(children:[Expanded(child:Text(_fieldLoadError!,
        style:TextStyle(color:Theme.of(context).colorScheme.error))),
        TextButton(onPressed:_fieldsLoading?null:_fetchFields,
          child:const Text('Повторить'))])),
    const SizedBox(height:10),DropdownButtonFormField<String>(initialValue:fields.any("""
assert s.count(old)==1, "field picker insertion anchor changed"
s=s.replace(old,new,1)
old=" @override void dispose(){username.dispose();"
new=" @override void dispose(){SessionService.instance.removeListener(_onFieldsUpdated);username.dispose();"
assert s.count(old)==1,"login dispose anchor changed"
s=s.replace(old,new,1)
# Prevent submitting an operator application with the old 'new' placeholder
# or a stale field ID after a network failure.
needle="try{await SessionService.instance.register("
assert s.count(needle)==1,"registration submission anchor changed"
replacement="""if(fieldId!='new'&&!SessionService.instance.approvedFields.any((f)=>f.id==fieldId)){
      setState(()=>error='Сначала выберите действующее месторождение.');return;
    }
    if(fieldId=='new'&&role!=UserRole.shopChief){
      setState(()=>error='Выберите месторождение из списка.');return;
    }
    try{await SessionService.instance.register("""
s=s.replace(needle,replacement,1)
p.write_text(s,encoding='utf-8')
assert s.count('SessionService.instance.addListener(_onFieldsUpdated)')==1
assert s.count('SessionService.instance.removeListener(_onFieldsUpdated)')==1
assert "_fieldManuallyChosen" in s
assert "onPressed:_fieldsLoading?null:_fetchFields" in s
print('PASS registration: existing field visible when async list arrives, retry on error, safe initial selection.')
