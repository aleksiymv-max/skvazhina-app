#!/usr/bin/env python3
"""v2.24: history uses the SAME captured measurement and well IDs as the walk.

Show all selected fields for oil/gas wells, including rline and ESP, with
distinct post-choke/Tpr temperatures. Archived wells are read from local
history without resurrecting deleted infrastructure in the production fund.
"""
from pathlib import Path

def one(s,a,b,label):
    n=s.count(a)
    if n!=1:raise AssertionError(f'{label}: wanted 1 anchor, got {n}')
    return s.replace(a,b,1)

db='lib/core/database/app_database.dart'
s=Path(db).read_text(encoding='utf8')
anchor='Future<Measurement?> latestForWell(String wellId) async {'
method="""Future<List<Map<String,String>>> archivedWellRefs(String fieldId) async {
  // Only this field's historical measurements. Does not resurrect a well.
  if(fieldId.isEmpty)return const <Map<String,String>>[];
  final db=await database;
  final active=<String>{for(final pad in demoPads)
    if(pad.fieldId==fieldId)for(final well in pad.wells)well.id};
  final rows=await db.rawQuery(
    'SELECT well_id,MAX(well_number) AS well_number,MAX(pad_id) AS pad_id '
    'FROM measurements WHERE field_id=? GROUP BY well_id '
    'ORDER BY MAX(measured_at) DESC LIMIT 500',[fieldId]);
  return rows.where((m)=>m['well_id']!=null &&
    !active.contains(m['well_id'].toString())).map((m)=><String,String>{
    'well_id':m['well_id'].toString(),
    'well_number':(m['well_number']??'—').toString(),
    'pad_id':(m['pad_id']??'').toString()}).toList();
}

"""
s=one(s,anchor,method+anchor,'archived well database reader')
Path(db).write_text(s,encoding='utf8')

repo='lib/core/repositories/measurement_repository.dart'
s=Path(repo).read_text(encoding='utf8')
anchor='Future<Measurement?> latestForWell(String id) => _database.latestForWell(id);'
s=one(s,anchor,anchor+"\nFuture<List<Map<String,String>>> archivedWellRefs(String fieldId)=>_database.archivedWellRefs(fieldId);",
      'repository history archive reader')
Path(repo).write_text(s,encoding='utf8')

path='lib/features/history/history_screen.dart'
s=Path(path).read_text(encoding='utf8')
start=s.index('List<(String,List<(String,String)>)> _historyBlocks(Measurement m)')
end=s.index('bool get _canEditAnnulus',start)
new=r"""List<(String,List<(String,String)>)> _historyBlocks(Measurement m){
 final out=<(String,List<(String,String)>)>[];
 void add(String title,List<(String,String)> rows){
  final visible=rows.where((r)=>r.$2.trim().isNotEmpty).toList();
  if(visible.isNotEmpty)out.add((title,visible));
 }
 bool recorded(String key,bool value)=>value&&
   (m.capturedParameters.isEmpty||m.capturedParameters.contains(key));
 final gas=well?.type==WellType.gasCondensate ||
   (well==null&&(m.rBuf!=null||m.tAfterChoke!=null)&&m.rz==null);
 add('Обход',[
  ('Скважина',m.wellNumber),
  ('Дата и время',DateFormat('dd.MM.yyyy HH:mm').format(m.measuredAt)),
  if(_txt(m.operatorName))('Оператор обхода',m.operatorName!),
  if(m.source!='Оператор')('Источник',m.source),
 ]);
 add('Давления',[
  if(recorded('rtr',m.rtr!=null))('Ртр',_f(m.rtr,_u(m,'rtr',gas?'МПа':'кгс/см²'))),
  if(recorded('rz',gas?m.rBuf!=null:m.rz!=null))
    ('Рз',_f(gas?m.rBuf:m.rz,_u(m,'rz',gas?'МПа':'кгс/см²'))),
  if(recorded('rline',m.rLine!=null))
    ('Рлин',_f(m.rLine,_u(m,'rline',gas?'МПа':'кгс/см²'))),
 ]);
 add('Температуры',[
  if(recorded('t_before',m.tBeforeChoke!=null))
    ('Т до штуцера',_f(m.tBeforeChoke,_u(m,'t_before','°C'))),
  if(recorded('t_after',m.tAfterChoke!=null||(gas&&m.tPed!=null)))
    ('Т после штуцера',_f(m.tAfterChoke??(gas?m.tPed:null),_u(m,'t_after','°C'))),
  if(recorded('t_line',m.tLine!=null))
    ('Тлин',_f(m.tLine,_u(m,'t_line','°C'))),
 ]);
 final hasPkv=m.capturedParameters.contains('pkv')||
   (m.capturedParameters.isEmpty&&(m.pkvInstalled||m.pkvWork!=null||m.pkvIdle!=null));
 if(hasPkv)add('ПКВ',[
  ('Программа установлена',m.pkvInstalled?'Да':'Нет'),
  if(m.pkvInstalled&&m.pkvWork!=null)
    ('Работа',_f(m.pkvWork!.toDouble(),_u(m,'pkv','мин'))),
  if(m.pkvInstalled&&m.pkvIdle!=null)
    ('Простой',_f(m.pkvIdle!.toDouble(),_u(m,'pkv','мин'))),
 ]);
 final hasPid=m.capturedParameters.contains('pid')||
   (m.capturedParameters.isEmpty&&(m.pidInstalled||m.pidCurrent!=null||_txt(m.pidFrequencyRange)));
 if(hasPid)add('ПИД',[
  ('Программа установлена',m.pidInstalled?'Да':'Нет'),
  if(m.pidInstalled&&m.pidCurrent!=null)
    ('Ток ПИД',_f(m.pidCurrent,_u(m,'pid','А'))),
  if(m.pidInstalled&&_txt(m.pidFrequencyRange))
    ('Диапазон F',m.pidFrequencyRange!),
 ]);
 add('Погружной датчик',[
  if(recorded('ruzd',m.rDownhole!=null))
    ('Рузд',_f(m.rDownhole,_u(m,'ruzd','МПа'))),
  if(recorded('tuzd',m.tDownhole!=null))
    ('Тузд',_f(m.tDownhole,_u(m,'tuzd','°C'))),
  if(recorded('rpr',m.rp!=null))
    ('Рпр',_f(m.rp,_u(m,'rpr','МПа'))),
  if(recorded('tpr',m.tPed!=null))
    ('Тпр',_f(m.tPed,_u(m,'tpr','°C'))),
 ]);
 add('Параметры ЭЦН',[
  if(recorded('esp_f',m.frequency!=null))
    ('F',_f(m.frequency,_u(m,'esp_f','Гц'))),
  if(recorded('esp_i',m.current!=null))
    ('Iср',_f(m.current,_u(m,'esp_i','А'))),
  if(recorded('esp_load',m.load!=null))
    ('Загрузка',_f(m.load,_u(m,'esp_load','%'))),
  if(recorded('esp_rins',m.rInsul!=null))
    ('Rизоляции',_f(m.rInsul,_u(m,'esp_rins','кОм'))),
 ]);
 if(m.capturedParameters.contains('choke')||
    (m.capturedParameters.isEmpty&&_txt(m.chokeMode)))
  add('Дросселирование',[
    if(_txt(m.chokeMode))('Тип',m.chokeMode!),
    if(m.chokeMode=='Дроссель'&&m.chokeValue!=null)
      ('Дроссель 1',_f(m.chokeValue,_u(m,'choke','%'))),
    if(m.chokeMode=='Дроссель'&&m.chokeValue2!=null)
      ('Дроссель 2',_f(m.chokeValue2,_u(m,'choke','%'))),
    if(m.chokeMode=='Штуцер'&&_txt(m.nozzle))
      ('Штуцер',m.nozzle!+' '+_u(m,'choke','мм')),
  ]);
 if(m.capturedParameters.contains('shutoff')||
    (m.capturedParameters.isEmpty&&(m.shutoffValveInstalled||m.rKo!=null)))
   add('Клапан-отсекатель',[
     ('Установлен',m.shutoffValveInstalled?'Да':'Нет'),
     if(m.shutoffValveInstalled&&m.rKo!=null)
       ('Рко',_f(m.rKo,_u(m,'shutoff','МПа'))),
   ]);
 if(m.capturedParameters.contains('inhibitor')||
    (m.capturedParameters.isEmpty&&(m.inhibitorInstalled||m.inhibitorFeed!=null)))
   add('Ингибитор',[
     ('Подача',m.inhibitorInstalled?'Да':'Нет'),
     if(m.inhibitorInstalled&&m.inhibitorFeed!=null)
       ('Расход',_f(m.inhibitorFeed,_u(m,'inhibitor','л/ч'))),
   ]);
 if(_txt(m.problemNote))add('Проблемы по скважине',[
   ('Описание',m.problemNote!),
 ]);
 return out;
}
"""
s=s[:start]+new+s[end:]
s=one(s,'List<Measurement> items = [];','List<Measurement> items = [];\nList<Map<String,String>> archivedWells = [];','archived selector state')
# Keep the archived list scoped to the active field and refreshed when the
# synced measurement database changes, not when an old pad is reintroduced.
anchor='void _remoteMeasurementsChanged(){if(mounted)_load();}'
s=one(s,anchor,
  '''Future<void> _loadArchivedWells()async{
  final requested=SessionService.instance.currentFieldId;
  if(requested==null||requested.isEmpty)return;
  try{
    final rows=await repo.archivedWellRefs(requested);
    if(!mounted||SessionService.instance.currentFieldId!=requested)return;
    setState(()=>archivedWells=rows);
  }catch(_){
    // Keep previously visible historical references during temporary errors.
  }
}
void _remoteMeasurementsChanged(){
 if(mounted){_load();_loadArchivedWells();}
}''','archived history refresh')
s=one(s,'items.clear();_hasMore=false;',
      'items.clear();_hasMore=false;archivedWells.clear();',
      'clear archived choices when user/field changes')
session_start=s.index('void _onSessionChanged(){')
session_end=s.index('void _filterHistoryDebounced()',session_start)
session_block=s[session_start:session_end]
assert session_block.count('_load();')==1,'expected one reload in session handler'
session_block=session_block.replace('_load();','_load();_loadArchivedWells();',1)
s=s[:session_start]+session_block+s[session_end:]
s=one(s,'MeasurementRepository.measurementRevision.addListener(_remoteMeasurementsChanged);_load();}',
      'MeasurementRepository.measurementRevision.addListener(_remoteMeasurementsChanged);_load();_loadArchivedWells();}',
      'initial archived well discovery')
s=one(s,"if (wellId == '__annulus__') _annulusParametersBlock()",
"""if(archivedWells.isNotEmpty)...[
 const SizedBox(height: 12),
 DropdownButtonFormField<String>(
   value:archivedWells.any((row)=>row['well_id']==wellId)?wellId:null,
   isExpanded:true,
   decoration:const InputDecoration(
     labelText:'Архивные скважины (не в текущем фонде)'),
   items:archivedWells.map((row)=>DropdownMenuItem<String>(
     value:row['well_id'],
     child:Text('Скважина '+(row['well_number']??'—')+
       ' · архив',overflow:TextOverflow.ellipsis))).toList(),
   onChanged:(v){
     if(v==null)return;
     setState((){
       wellId=v;selectedDate=null;items=[];_hasMore=false;
     });
     _load();
   }),
],
if (wellId == '__annulus__') _annulusParametersBlock()""",
      'archived selector UI')
s=one(s,"if (well != null) Text('Замеры скважины ${well!.number}', style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w800)),",
      """if (well != null) Text('Замеры скважины '+well!.number, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w800)),
if(well==null&&archivedWells.any((row)=>row['well_id']==wellId))
  const Text('Архивные замеры исключённой из фонда скважины',
    style:TextStyle(fontSize:16,fontWeight:FontWeight.w700)),""",
      'archived history heading')
Path(path).write_text(s,encoding='utf8')

about=Path('lib/features/menu/about_screen.dart')
t=about.read_text(encoding='utf8')
assert t.count('Версия v2.23')==2, 'unexpected application release metadata'
about.write_text(t.replace('Версия v2.23','Версия v2.24'),encoding='utf8')
print('PASS v2.24: history includes rline/ESP and distinct temperatures, independent well IDs, archived-only read')
