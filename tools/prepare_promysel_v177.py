from pathlib import Path
import re
r=Path.cwd()
p=r/'lib/features/history/history_screen.dart'
s=p.read_text()
start=s.index('  Widget _details(Measurement m) {')
end=s.index('  bool get _canEditAnnulus',start)
new=r'''  Widget _details(Measurement m) {
    final blocks=_historyBlocks(m);
    return Padding(
      padding:const EdgeInsets.fromLTRB(12,0,12,14),
      child:Column(crossAxisAlignment:CrossAxisAlignment.stretch,children:[
        const Divider(),
        ...blocks.map((b)=>Card(
          margin:const EdgeInsets.only(bottom:10),
          child:Padding(
            padding:const EdgeInsets.all(14),
            child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[
              Text(b.$1,style:const TextStyle(fontWeight:FontWeight.w800,fontSize:16)),
              const SizedBox(height:8),
              ...b.$2.map((e)=>Padding(
                padding:const EdgeInsets.symmetric(vertical:5),
                child:Row(crossAxisAlignment:CrossAxisAlignment.start,children:[
                  Expanded(child:Text(e.$1,style:TextStyle(color:Theme.of(context).colorScheme.onSurfaceVariant))),
                  const SizedBox(width:12),
                  Expanded(child:Text(e.$2,style:const TextStyle(fontWeight:FontWeight.w700))),
                ]),
              )),
            ]),
          ),
        )),
        if(SessionService.instance.currentUser.canCorrect)...[
          const SizedBox(height:4),
          FilledButton.icon(onPressed:()async{final changed=await Navigator.push<bool>(context,MaterialPageRoute(builder:(_)=>CorrectionScreen(measurement:m)));if(changed==true)_load();},icon:const Icon(Icons.edit_outlined),label:const Text('Корректировать параметры')),
        ],
      ]),
    );
  }

  String _f(double? v,String u)=>v==null?'':('${v.toStringAsFixed(v.truncateToDouble()==v?0:2).replaceAll('.',',')}${u.trim().isEmpty?'':' $u'}');
  String _u(Measurement m,String key,String fallback){final v=m.capturedUnits[key]?.trim();return v==null||v.isEmpty?fallback:v;}
  bool _cap(Measurement m,String key)=>m.capturedParameters.contains(key);
  bool _textValue(String? v)=>v!=null&&v.trim().isNotEmpty;
  List<(String,List<(String,String)>)> _historyBlocks(Measurement m){
    final out=<(String,List<(String,String)>)>[];
    void add(String title,List<(String,String)> rows){final clean=rows.where((e)=>e.$2.trim().isNotEmpty).toList();if(clean.isNotEmpty)out.add((title,clean));}
    add('Обход',[('Дата и время',DateFormat('dd.MM.yyyy HH:mm').format(m.measuredAt)),if(_textValue(m.operatorName))('Оператор обхода',m.operatorName!)]);
    if(well?.type==WellType.gasCondensate){
      add('Давления',[
        if(_cap(m,'rtr')&&m.rtr!=null)('Ртр',_f(m.rtr,_u(m,'rtr','МПа'))),
        if(_cap(m,'rz')&&m.rBuf!=null)('Рз',_f(m.rBuf,_u(m,'rz','МПа'))),
        if(_cap(m,'rline')&&m.rLine!=null)('Рлин',_f(m.rLine,_u(m,'rline','МПа'))),
      ]);
      add('Температуры',[
        if(_cap(m,'t_before')&&m.tBeforeChoke!=null)('Т до штуцера',_f(m.tBeforeChoke,_u(m,'t_before','°C'))),
        if(_cap(m,'t_after')&&m.tPed!=null)('Т после штуцера',_f(m.tPed,_u(m,'t_after','°C'))),
        if(_cap(m,'t_line')&&m.tLine!=null)('Тлин',_f(m.tLine,_u(m,'t_line','°C'))),
      ]);
      if(_cap(m,'choke'))add('Дросселирование',[
        if(_textValue(m.chokeMode))('Тип',m.chokeMode!),
        if(m.chokeMode=='Дроссель'&&m.chokeValue!=null)('Дроссель 1',_f(m.chokeValue,_u(m,'choke','%'))),
        if(m.chokeMode=='Дроссель'&&m.chokeValue2!=null)('Дроссель 2',_f(m.chokeValue2,_u(m,'choke','%'))),
        if(m.chokeMode=='Штуцер'&&_textValue(m.nozzle))('Штуцер','${m.nozzle!}${_u(m,'choke','мм').trim().isEmpty?'':' ${_u(m,'choke','мм')}'}'),
      ]);
      add('Погружной датчик',[
        if(_cap(m,'ruzd')&&m.rDownhole!=null)('Рузд',_f(m.rDownhole,_u(m,'ruzd','МПа'))),
        if(_cap(m,'tuzd')&&m.tDownhole!=null)('Тузд',_f(m.tDownhole,_u(m,'tuzd','°C'))),
        if(_cap(m,'rpr')&&m.rp!=null)('Рпр',_f(m.rp,_u(m,'rpr','МПа'))),
        if(_cap(m,'tpr')&&m.tPed!=null)('Тпр',_f(m.tPed,_u(m,'tpr','°C'))),
      ]);
      if(_cap(m,'shutoff'))add('Клапан-отсекатель',[('Установлен',m.shutoffValveInstalled?'Да':'Нет'),if(m.shutoffValveInstalled&&m.rKo!=null)('Рко',_f(m.rKo,_u(m,'shutoff','МПа')))]);
      if(_cap(m,'inhibitor'))add('Ингибитор',[('Подача',m.inhibitorInstalled?'Да':'Нет'),if(m.inhibitorInstalled&&m.inhibitorFeed!=null)('Расход',_f(m.inhibitorFeed,_u(m,'inhibitor','л/ч')))]);
    }else{
      add('Давления',[
        if(_cap(m,'rtr')&&m.rtr!=null)('Ртр',_f(m.rtr,_u(m,'rtr','кгс/см²'))),
        if(_cap(m,'rz')&&m.rz!=null)('Рз',_f(m.rz,_u(m,'rz','кгс/см²'))),
      ]);
      if(_cap(m,'pkv'))add('ПКВ',[('Программа установлена',m.pkvInstalled?'Да':'Нет'),if(m.pkvInstalled&&m.pkvWork!=null)('Работа',_f(m.pkvWork!.toDouble(),_u(m,'pkv','мин'))),if(m.pkvInstalled&&m.pkvIdle!=null)('Простой',_f(m.pkvIdle!.toDouble(),_u(m,'pkv','мин')))]);
      if(_cap(m,'pid'))add('ПИД',[('Программа установлена',m.pidInstalled?'Да':'Нет'),if(m.pidInstalled&&m.pidCurrent!=null)('Ток ПИД',_f(m.pidCurrent,_u(m,'pid','А'))),if(m.pidInstalled&&_textValue(m.pidFrequencyRange))('Диапазон F',m.pidFrequencyRange!)]);
      add('Погружной датчик',[if(_cap(m,'rpr')&&m.rp!=null)('Рпр',_f(m.rp,_u(m,'rpr','МПа'))),if(_cap(m,'tpr')&&m.tPed!=null)('Тпр',_f(m.tPed,_u(m,'tpr','°C')))]);
      add('Параметры ЭЦН',[
        if(_cap(m,'esp_f')&&m.frequency!=null)('F',_f(m.frequency,_u(m,'esp_f','Гц'))),
        if(_cap(m,'esp_i')&&m.current!=null)('Iср',_f(m.current,_u(m,'esp_i','А'))),
        if(_cap(m,'esp_load')&&m.load!=null)('Загрузка',_f(m.load,_u(m,'esp_load','%'))),
        if(_cap(m,'esp_rins')&&m.rInsul!=null)('Rизоляции',_f(m.rInsul,_u(m,'esp_rins','кОм'))),
      ]);
    }
    if(_textValue(m.problemNote))add('Проблемы по скважине',[('Описание',m.problemNote!)]);
    return out;
  }

'''
s=s[:start]+new+s[end:]
p.write_text(s)
# Version bump.
pub=r/'pubspec.yaml';ps=pub.read_text();ps=re.sub(r'version:\s*[^\n]+','version: 1.77.0+183',ps,count=1);pub.write_text(ps)
# Deterministic gates: History must depend only on the saved walk snapshot, never live config.
h=p.read_text()
assert 'm.capturedParameters.contains(key)' in h
assert 'WalkParameterConfig.instance.on(m.padId,key)' not in h
assert "add('Давления'" in h and "add('Температуры'" in h and "add('Дросселирование'" in h and "add('Параметры ЭЦН'" in h
assert "if(_cap(m,'rtr')&&m.rtr!=null)" in h
print('v1.77 history = saved walk snapshot, same blocks, empty values omitted',flush=True)
