import 'package:flutter/material.dart';
import '../../core/models/production_area.dart';
import '../../core/models/pad.dart';
import '../../core/models/well.dart';
import '../../core/services/session_service.dart';
import '../../core/services/sync_service.dart';
import '../../core/services/app_state_store.dart';
import '../../core/services/field_problem_report_store.dart';

/// An issue can concern a whole pad. Saving it must not create a walkthrough.
class FieldProblemFormScreen extends StatefulWidget {
 const FieldProblemFormScreen({super.key});
 @override State<FieldProblemFormScreen> createState()=>_FieldProblemFormScreenState();
}
class _FieldProblemFormScreenState extends State<FieldProblemFormScreen> {
 final _form=GlobalKey<FormState>();
 final _description=TextEditingController();
 String? _areaId,_padId,_wellId;
 bool _saving=false;
 @override void initState(){
  super.initState();
  // Populate open selectors when delayed sync or session switch updates cache.
  structureRevision.addListener(_refreshStructure);
  SyncService.instance.addListener(_refreshStructure);
  SessionService.instance.addListener(_refreshStructure);
 }
 void _refreshStructure(){
  if(!mounted)return;
  final field=SessionService.instance.currentFieldId;
  final area=_areasFor(field).where((a)=>a.id==_areaId).firstOrNull;
  final pad=_padsFor(field,area).where((p)=>p.id==_padId).firstOrNull;
  setState((){
   if(area==null){_areaId=null;_padId=null;_wellId=null;}
   else if(pad==null){_padId=null;_wellId=null;}
   else if(_wellId!=null&&!pad.wells.any((w)=>w.id==_wellId)){_wellId=null;}
  });
 }
 // Only cached objects within the selected field are selectable.
 // Some older local snapshots contain pads before their area list: their
 // real areaId/areaName allow a form-only fallback without creating records.
 List<ProductionArea> _areasFor(String? fid){
  if(fid==null||fid.isEmpty)return <ProductionArea>[];
  final areas=demoAreas.where((a)=>a.fieldId==fid).toList();
  final known=areas.map((a)=>a.id).toSet();
  for(final p in demoPads.where((p)=>p.fieldId==fid)){
   if(p.areaId.isEmpty||p.areaName.trim().isEmpty||!known.add(p.areaId))continue;
   areas.add(ProductionArea(id:p.areaId,name:p.areaName,
    padIds:demoPads.where((x)=>x.fieldId==fid&&x.areaId==p.areaId)
      .map((x)=>x.id).toList(),fieldId:fid));
  }
  return areas;
 }
 List<Pad> _padsFor(String? fid,ProductionArea? area){
  if(fid==null||area==null)return <Pad>[];
  return demoPads.where((p)=>p.fieldId==fid&&
    (p.areaId==area.id||area.padIds.contains(p.id))).toList();
 }
 @override void dispose(){
  SessionService.instance.removeListener(_refreshStructure);
  SyncService.instance.removeListener(_refreshStructure);
  structureRevision.removeListener(_refreshStructure);
  _description.dispose();
  super.dispose();
 }
 Future<void> _submit() async {
  if(_saving||!(_form.currentState?.validate()??false))return;
  final field=SessionService.instance.currentFieldId;
  final area=_areasFor(field).where((a)=>a.id==_areaId).firstOrNull;
  final pad=_padsFor(field,area).where((p)=>p.id==_padId).firstOrNull;
  final well=pad?.wells.where((w)=>w.id==_wellId).firstOrNull;
  if(field==null||area==null||pad==null){
   ScaffoldMessenger.of(context).showSnackBar(
    const SnackBar(content:Text('Обязательно выберите участок и куст')));
   return;
  }
  setState(()=>_saving=true);
  try {
   await FieldProblemReportStore.instance.create(
    fieldId:field,areaId:area.id,areaName:area.name,
    padId:pad.id,padName:pad.name,
    wellId:well?.id,wellNumber:well?.number,
    description:_description.text);
   if(!mounted)return;
   ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
    content:Text('Заявка сохранена. Она появится в «Проблемах»; при отсутствии сети отправится позже.')));
   Navigator.of(context).pop();
  }catch(_){
   if(!mounted)return;
   ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
    content:Text('Не удалось сохранить заявку на устройстве. Попробуйте ещё раз.')));
  }finally{if(mounted)setState(()=>_saving=false);}
 }
 @override Widget build(BuildContext context) {
  final fid=SessionService.instance.currentFieldId;
  final areas=_areasFor(fid);
  final area=areas.where((a)=>a.id==_areaId).firstOrNull;
  final pads=_padsFor(fid,area);
  final pad=pads.where((p)=>p.id==_padId).firstOrNull;
  final wells=pad?.wells??<Well>[];
  return Scaffold(
   appBar:AppBar(title:const Text('Подать заявку')),
   body:Form(key:_form,child:ListView(
    padding:const EdgeInsets.fromLTRB(16,16,16,36),children:[
     const Text('Сообщить о производственной проблеме',
      style:TextStyle(fontSize:20,fontWeight:FontWeight.w800)),
     const SizedBox(height:8),
     const Text('Заявка создаётся отдельно от обхода скважины. '
      'Можно указать проблему, относящуюся ко всему кусту.'),
     const SizedBox(height:22),
     if(areas.isEmpty)...[
      const DecoratedBox(
       decoration:BoxDecoration(color:Color(0xFFFFF4E5),
        borderRadius:BorderRadius.all(Radius.circular(10))),
       child:Padding(padding:EdgeInsets.all(12),
        child:Text('Участки месторождения ещё не загружены на '
         'это устройство. Подключитесь к сети и дождитесь '
         'синхронизации. Уже сохранённые участки доступны '
         'без интернета; не очищайте данные браузера.',
         style:TextStyle(color:Color(0xFF6B4300))))),
      const SizedBox(height:12),
     ],
     DropdownButtonFormField<String>(
      key:const ValueKey('problem-area'),initialValue:_areaId,
      isExpanded:true,
      decoration:const InputDecoration(labelText:'Участок добычи *',
       border:OutlineInputBorder()),
      items:areas.map((a)=>DropdownMenuItem<String>(
       value:a.id,child:Text(a.name,overflow:TextOverflow.ellipsis))).toList(),
      onChanged:_saving||areas.isEmpty?null:(v)=>setState((){_areaId=v;_padId=null;_wellId=null;}),
      validator:(v)=>v==null?'Выберите участок':null,
     ),
     const SizedBox(height:16),
     DropdownButtonFormField<String>(
      key:ValueKey('problem-pad-${_areaId??"none"}'),initialValue:_padId,
      isExpanded:true,
      decoration:const InputDecoration(labelText:'Кустовая площадка *',
       border:OutlineInputBorder()),
      items:pads.map((p)=>DropdownMenuItem<String>(
       value:p.id,child:Text(p.name,overflow:TextOverflow.ellipsis))).toList(),
      onChanged:_saving||pads.isEmpty?null:(v)=>setState((){_padId=v;_wellId=null;}),
      validator:(v)=>v==null?'Выберите куст':null,
     ),
     const SizedBox(height:16),
     DropdownButtonFormField<String>(
      key:ValueKey('problem-well-${_padId??"none"}'),initialValue:_wellId,
      isExpanded:true,
      decoration:const InputDecoration(labelText:'Скважина (необязательно)',
       border:OutlineInputBorder()),
      hint:const Text('Весь куст — без скважины'),
      items:[
       const DropdownMenuItem<String>(value:'',child:Text('Весь куст — без скважины')),
       ...wells.map((w)=>DropdownMenuItem<String>(
        value:w.id,child:Text('Скважина ${w.number}')))
      ],
      onChanged:_saving||pad==null?null:(v)=>
        setState(()=>_wellId=(v==null||v.isEmpty)?null:v),
     ),
     const SizedBox(height:16),
     TextFormField(controller:_description,
      maxLines:5,minLines:3,maxLength:2000,
      textCapitalization:TextCapitalization.sentences,
      decoration:const InputDecoration(
       labelText:'Описание проблемы *',alignLabelWithHint:true,
       hintText:'Что произошло, где обнаружено и что требуется проверить?',
       border:OutlineInputBorder()),
      validator:(value){
       final text=(value??'').trim();
       if(text.isEmpty)return 'Опишите проблему';
       if(text.length<3)return 'Описание слишком короткое';
       return null;
      },
     ),
     const SizedBox(height:10),
     const Text('* Обязательные поля',
      style:TextStyle(fontSize:12)),
     const SizedBox(height:12),
     FilledButton.icon(
      onPressed:_saving||areas.isEmpty?null:_submit,
      icon:_saving?const SizedBox(width:18,height:18,
        child:CircularProgressIndicator(strokeWidth:2)):
        const Icon(Icons.send_outlined),
      label:Text(_saving?'Сохранение заявки…':'Подать заявку'),
     ),
     const SizedBox(height:12),
     const Text('После сохранения заявка отображается на главной странице '
      'в разделе «Проблемы». При слабой связи запись остаётся на устройстве.',
      style:TextStyle(height:1.45,fontSize:13)),
    ])),
  );
 }
}
