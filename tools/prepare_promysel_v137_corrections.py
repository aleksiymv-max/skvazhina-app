from pathlib import Path
r=Path.cwd()
def edit(p,f):
 q=r/p;x=q.read_text();q.write_text(f(x))

# Repository exposes audit rows for a measurement.
edit('lib/core/repositories/measurement_repository.dart',lambda x:x.replace(
"  Future<int> correct({required int measurementId,required String parameter,required String? newValue,required String userId,required String userName,required String reason,String? comment}) => _database.correctMeasurement(measurementId:measurementId,parameter:parameter,newValue:newValue,userId:userId,userName:userName,reason:reason,comment:comment);",
"  Future<int> correct({required int measurementId,required String parameter,required String? newValue,required String userId,required String userName,required String reason='',String? comment}) => _database.correctMeasurement(measurementId:measurementId,parameter:parameter,newValue:newValue,userId:userId,userName:userName,reason:reason,comment:comment);\n  Future<List<Map<String,Object?>>> auditForMeasurement(int id)=>_database.auditForMeasurement(id);"))

# Correction screen: no reason/comment fields; audit metadata is automatic.
def correction(x):
 x=x.replace("  final reason = TextEditingController();\n  final comment = TextEditingController();\n","")
 start="        const SizedBox(height: 10),\n        TextField(controller: reason, decoration: const InputDecoration(labelText: 'Причина исправления *')),\n        const SizedBox(height: 10),\n        TextField(controller: comment, maxLines: 2, decoration: const InputDecoration(labelText: 'Комментарий')),\n"
 x=x.replace(start,"        const SizedBox(height: 10),\n        Text('Изменение будет сохранено в истории автоматически с ФИО и датой.',style:Theme.of(context).textTheme.bodySmall),\n")
 x=x.replace("    if (reason.text.trim().isEmpty) { ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Укажите причину исправления'))); return; }\n","")
 x=x.replace("reason: reason.text.trim(), comment: comment.text.trim().isEmpty ? null : comment.text.trim()","reason: ''")
 x=x.replace("value.dispose(); reason.dispose(); comment.dispose();","value.dispose();")
 return x
edit('lib/features/corrections/correction_screen.dart',correction)

# History: render audit changes old red -> new green with editor and timestamp.
def history(x):
 old="""  Widget _details(Measurement m) {
    final rows = _all(m);
    return Padding(padding: const EdgeInsets.fromLTRB(16, 0, 16, 16), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      const Divider(),
      ...rows.map((e) => Padding(padding: const EdgeInsets.symmetric(vertical: 4), child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [Expanded(child: Text(e.$1, style: TextStyle(color: Theme.of(context).colorScheme.onSurfaceVariant))), Expanded(flex: 2, child: Text(e.$2, style: const TextStyle(fontWeight: FontWeight.w600)))]))),
      if (SessionService.instance.currentUser.canCorrect) ...[
        const SizedBox(height: 10),
        SizedBox(width: double.infinity, child: FilledButton.icon(onPressed: () async { final changed = await Navigator.push<bool>(context, MaterialPageRoute(builder: (_) => CorrectionScreen(measurement: m))); if (changed == true) _load(); }, icon: const Icon(Icons.edit_outlined), label: const Text('Корректировать параметры'))),
      ],
    ]));
  }
"""
 new="""  Widget _details(Measurement m) {
    final rows = _all(m);
    return FutureBuilder<List<Map<String,Object?>>>(
      future:m.id==null?Future.value(const []):repo.auditForMeasurement(m.id!),
      builder:(context,snap){
        final audit=<String,Map<String,Object?>>{};
        for(final a in snap.data??const <Map<String,Object?>>[]){final p=a['parameter']?.toString();if(p!=null&&p!='problem_resolved')audit.putIfAbsent(p,()=>a);}
        return Padding(padding:const EdgeInsets.fromLTRB(16,0,16,16),child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[
          const Divider(),
          ...rows.map((e){final key=_parameterKey(e.$1);final a=key==null?null:audit[key];return Padding(padding:const EdgeInsets.symmetric(vertical:5),child:Row(crossAxisAlignment:CrossAxisAlignment.start,children:[
            Expanded(child:Text(e.$1,style:TextStyle(color:Theme.of(context).colorScheme.onSurfaceVariant))),
            Expanded(flex:2,child:a==null?Text(e.$2,style:const TextStyle(fontWeight:FontWeight.w600)):Column(crossAxisAlignment:CrossAxisAlignment.start,children:[
              Wrap(crossAxisAlignment:WrapCrossAlignment.center,spacing:6,children:[
                Text(_auditValue(a['old_value']?.toString()),style:const TextStyle(color:Colors.red,fontWeight:FontWeight.w800,decoration:TextDecoration.lineThrough)),
                const Icon(Icons.arrow_forward,size:16),
                Text(e.$2,style:const TextStyle(color:Colors.green,fontWeight:FontWeight.w900)),
              ]),
              const SizedBox(height:2),
              Text(_auditCaption(a),style:Theme.of(context).textTheme.bodySmall?.copyWith(fontSize:10)),
            ])),
          ]));}),
          if(SessionService.instance.currentUser.canCorrect)...[
            const SizedBox(height:10),
            SizedBox(width:double.infinity,child:FilledButton.icon(onPressed:()async{final changed=await Navigator.push<bool>(context,MaterialPageRoute(builder:(_)=>CorrectionScreen(measurement:m)));if(changed==true)_load();},icon:const Icon(Icons.edit_outlined),label:const Text('Корректировать параметры'))),
          ],
        ]));
      },
    );
  }

  String _auditValue(String? v){if(v==null||v.isEmpty)return '—';if(v=='1')return 'Да';if(v=='0')return 'Нет';return v.replaceAll('.',',');}
  String _auditCaption(Map<String,Object?> a){final dt=DateTime.tryParse(a['created_at']?.toString()??'');final d=dt==null?'':DateFormat('dd.MM.yyyy HH:mm').format(dt.toLocal());return '${a['user_name']??'—'} · $d';}
  String? _parameterKey(String label){
    const m=<String,String>{'Рбуф':'r_buf','Ртр':'rtr','Рз':'rz','Рлин':'r_line','Тдо штуцера':'t_before_choke','Т до штуцера':'t_before_choke','Тлин':'t_line','Дросселирование':'choke_mode','Дроссель 1':'choke_value','Дроссель 2':'choke_value2','Штуцер':'nozzle','Подземная телеметрия: Рузд':'r_downhole','Подземная телеметрия: Тузд':'t_downhole','Клапан-отсекатель':'shutoff_valve_installed','Рко':'r_ko','Ингибитор':'inhibitor_installed','Расход ингибитора':'inhibitor_feed','ПКВ установлена':'pkv_installed','ПКВ: работа':'pkv_work','ПКВ: простой':'pkv_idle','ПИД установлена':'pid_installed','Ток ПИД':'pid_current','Диапазон F':'pid_frequency_range','F':'frequency','Iср':'current','Загрузка':'load','Рпр':'rp','Тпэд':'t_ped','Rизол':'r_insul','Проблема':'problem_note'};return m[label];
  }
"""
 if old not in x: raise Exception('details marker not found')
 return x.replace(old,new)
edit('lib/features/history/history_screen.dart',history)
