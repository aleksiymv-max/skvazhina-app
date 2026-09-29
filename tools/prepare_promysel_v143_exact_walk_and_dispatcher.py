from pathlib import Path
r=Path.cwd()

# v1.43 - deterministic fixes after inspecting the generated v1.42 source.

# 1. Well walk form: the selected area configuration is the only source of visible blocks.
p=r/'lib/features/wells/well_screen.dart'; x=p.read_text()
start=x.index("  Scaffold _oil()=>")
end=x.index("\n  Widget _problem()=>",start)
forms=r"""  List<Widget> _configuredBlocks(){
    final blocks=<Widget>[];
    if(showP('rtr')||showP('rz')||showP('rline'))blocks.add(_section('Давления',[
      if(showP('rtr'))_number('Ртр',rtr,well.type==WellType.gasCondensate?'МПа':'кгс/см²'),
      if(showP('rz'))_number('Рз',well.type==WellType.gasCondensate?rBuf:rz,well.type==WellType.gasCondensate?'МПа':'кгс/см²'),
      if(showP('rline'))_number('Рлин',rLine,well.type==WellType.gasCondensate?'МПа':'кгс/см²'),
    ]));
    if(showP('t_before')||showP('t_after')||showP('t_line'))blocks.add(_section('Температуры',[
      if(showP('t_before'))_number('Т до штуцера',tBeforeChoke,'°C'),
      if(showP('t_after'))_number('Т после штуцера',tPed,'°C'),
      if(showP('t_line'))_number('Тлин',tLine,'°C'),
    ]));
    if(showP('pkv'))blocks.add(_section('ПКВ',[CheckboxListTile(contentPadding:EdgeInsets.zero,value:pkvInstalled,onChanged:(v)=>setState((){pkvInstalled=v??false;pkvConfirmed=true;}),title:const Text('Программа ПКВ установлена')),if(pkvInstalled)_row(_number('Работа',pkvWork,'мин',integer:true),_number('Простой',pkvIdle,'мин',integer:true))]));
    if(showP('pid'))blocks.add(_section('ПИД',[CheckboxListTile(contentPadding:EdgeInsets.zero,value:pidInstalled,onChanged:(v)=>setState((){pidInstalled=v??false;pidConfirmed=true;}),title:const Text('Программа ПИД установлена')),if(pidInstalled)_row(_number('Ток ПИД',pidCurrent,'А'),_text('Диапазон F',pidFrequencyRange,'Например 40–60 Гц'))]));
    if(showP('choke'))blocks.add(_section('Дросселирование',[SegmentedButton<String>(segments:const[ButtonSegment(value:'Штуцер',label:Text('Штуцер')),ButtonSegment(value:'Дроссель',label:Text('Дроссель'))],selected:{chokeMode},onSelectionChanged:(v)=>setState(()=>chokeMode=v.first)),const SizedBox(height:10),if(chokeMode=='Дроссель')_row(_number('Дроссель 1',choke1,'%',integer:true),_number('Дроссель 2',choke2,'%',integer:true))else _text('Штуцер',nozzle,'Сечение штуцера')]));
    if(showP('ruzd')||showP('tuzd')||showP('rpr')||showP('tpr'))blocks.add(_section('Погружной датчик',[
      if(showP('ruzd'))_number('Рузд',rDownhole,'МПа'),if(showP('tuzd'))_number('Тузд',tDownhole,'°C'),if(showP('rpr'))_number('Рпр',rp,'МПа'),if(showP('tpr'))_number('Тпр',tPed,'°C'),
    ]));
    if(showP('esp_f')||showP('esp_i')||showP('esp_load')||showP('esp_rins'))blocks.add(_section('Параметры ЭЦН',[
      if(showP('esp_f'))_number('F',frequency,'Гц'),if(showP('esp_i'))_number('Iср',current,'А'),if(showP('esp_load'))_number('Загрузка',load,'%'),if(showP('esp_rins'))_number('Rизоляции',rInsul,'кОм'),
    ]));
    if(showP('shutoff'))blocks.add(_section('Клапан-отсекатель',[SwitchListTile(contentPadding:EdgeInsets.zero,value:shutoffValveInstalled,onChanged:(v)=>setState(()=>shutoffValveInstalled=v),title:const Text('Клапан-отсекатель установлен')),if(shutoffValveInstalled)_number('Рко',rKo,'МПа')]));
    if(showP('inhibitor'))blocks.add(_section('Ингибитор',[SwitchListTile(contentPadding:EdgeInsets.zero,value:inhibitorInstalled,onChanged:(v)=>setState(()=>inhibitorInstalled=v),title:const Text('Подача ингибитора')),if(inhibitorInstalled)_number('Расход',inhibitorFeed,'л/ч')]));
    return blocks;
  }
  Scaffold _oil()=>_configuredScaffold();
  Scaffold _gas()=>_configuredScaffold();
  Scaffold _configuredScaffold()=>Scaffold(appBar:AppBar(title:Text('Скважина ${well.number}'),bottom:_walk()),body:Form(key:formKey,child:ListView(padding:const EdgeInsets.fromLTRB(16,4,16,28),children:[_statusSelector(),..._configuredBlocks(),_problem(),_save()])));
"""
x=x[:start]+forms+x[end:];p.write_text(x)

# 2. Dispatcher problem card: keep the responsive v1.42 card; dispatcher role detection is already patched there.\n\n# 3. Restore task/problem journals with their real named signatures.
p=r/'lib/features/history/history_screen.dart'; x=p.read_text()
x=x.replace("ExportService.createTaskJournalXlsx(WorkTaskStore.instance.tasks)","ExportService.createTaskJournalXlsx(tasks:WorkTaskStore.instance.tasks)")
x=x.replace("ExportService.createProblemJournalXlsx(rows)","ExportService.createProblemJournalXlsx(problems:rows)")
p.write_text(x)

# Version.
p=r/'pubspec.yaml'; x=p.read_text(); import re
x=re.sub(r'version: 1\.41\.0\+145','version: 1.43.0+147',x);p.write_text(x)
