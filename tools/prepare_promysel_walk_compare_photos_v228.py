#!/usr/bin/env python3
"""v2.28: last measurement header, compact deltas, original-ratio chat photos."""
from pathlib import Path

def one(s,a,b,label):
 n=s.count(a)
 if n!=1:raise RuntimeError(f'v2.28 {label}: expected one, got {n}')
 return s.replace(a,b,1)

p=Path('lib/features/wells/well_screen.dart')
s=p.read_text(encoding='utf-8')
s=one(s,'  Future<void> _loadLatest() async {',
'''  Measurement? _previousMeasurement;
  Future<void> _loadLatest() async {''','previous measurement variable')
s=one(s,
'    final m = await repository.latestForWell(widget.wellId);',
'''    // Same well, same pad and signed-in field; exactly one local DB read.
    final rows=await repository.history(
      padId:widget.padId,wellId:widget.wellId,limit:1);
    final m=rows.isEmpty?null:rows.first;
    _previousMeasurement=m;''','previous reading scoped query')
s=one(s,
'children:[_statusSelector(),..._configuredBlocks(),_problem(),_save()]',
'children:[_previousHeader(),_statusSelector(),..._configuredBlocks(),_problem(),_save()]',
'previous reading top banner')
header=r"""  String _priorTime(DateTime t){
    final d=t.toLocal();
    String pad(int n)=>n.toString().padLeft(2,'0');
    return pad(d.day)+'.'+pad(d.month)+'.'+d.year.toString()+
      ' · '+pad(d.hour)+':'+pad(d.minute);
  }
  Widget _previousHeader(){
    final last=_previousMeasurement;
    if(last==null)return const Padding(padding:EdgeInsets.fromLTRB(4,8,4,12),
      child:Text('Предыдущий замер отсутствует',
        style:TextStyle(fontSize:11,color:Colors.grey)));
    final worker=last.operatorName?.trim();
    return Padding(padding:const EdgeInsets.fromLTRB(4,6,4,12),
      child:Row(crossAxisAlignment:CrossAxisAlignment.start,children:[
        const Icon(Icons.history_rounded,size:17,color:Colors.blueGrey),
        const SizedBox(width:8),
        Expanded(child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[
          Text('Прошлый замер · '+_priorTime(last.measuredAt),
            style:const TextStyle(fontSize:12,fontWeight:FontWeight.w700)),
          const SizedBox(height:2),
          Text('Выполнил: '+(worker==null||worker.isEmpty?'Не указан':worker),
            maxLines:2,overflow:TextOverflow.ellipsis,
            style:TextStyle(fontSize:11,
              color:Theme.of(context).colorScheme.onSurfaceVariant))
        ]))
      ]));
  }
  double? _priorNumber(TextEditingController c,Measurement m){
    if(identical(c,rtr))return m.rtr;
    if(identical(c,rz))return m.rz;
    if(identical(c,pkvWork))return m.pkvWork?.toDouble();
    if(identical(c,pkvIdle))return m.pkvIdle?.toDouble();
    if(identical(c,pidCurrent))return m.pidCurrent;
    if(identical(c,frequency))return m.frequency;
    if(identical(c,current))return m.current;
    if(identical(c,load))return m.load;
    if(identical(c,rp))return m.rp;
    if(identical(c,tPed))return m.tPed;
    if(identical(c,tAfterChoke))return m.tAfterChoke ??
      (well.type==WellType.gasCondensate?m.tPed:null);
    if(identical(c,rInsul))return m.rInsul;
    if(identical(c,rBuf))return m.rBuf;
    if(identical(c,rLine))return m.rLine;
    if(identical(c,tBeforeChoke))return m.tBeforeChoke;
    if(identical(c,tLine))return m.tLine;
    if(identical(c,choke1))return m.chokeValue;
    if(identical(c,choke2))return m.chokeValue2;
    if(identical(c,nozzle))return PromyselDecimalInput.parse(m.nozzle??'');
    if(identical(c,rDownhole))return m.rDownhole;
    if(identical(c,tDownhole))return m.tDownhole;
    if(identical(c,rKo))return m.rKo;
    if(identical(c,inhibitorFeed))return m.inhibitorFeed;
    return null;
  }
  String _shortValue(double value){
    if(value.abs()<0.005)return '0';
    return value.toStringAsFixed(2).replaceFirst(
      RegExp(r'\.?0+$'),'').replaceAll('.',',');
  }
  Widget _previousDelta(TextEditingController c,{required bool enabled}){
    final previous=_previousMeasurement;
    if(!enabled||previous==null)return const SizedBox.shrink();
    final old=_priorNumber(c,previous);
    if(old==null||!old.isFinite)return const SizedBox.shrink();
    return Padding(padding:const EdgeInsets.only(top:3,left:4,right:2),
      child:ValueListenableBuilder<TextEditingValue>(
        valueListenable:c,builder:(context,input,_){
          final current=PromyselDecimalInput.parse(input.text);
          final d=current==null||!current.isFinite?null:current-old;
          final direction=d==null||d.abs()<0.005?0:(d>0?1:-1);
          final color=direction>0?Colors.green.shade700:
            direction<0?Colors.red.shade700:
            Theme.of(context).colorScheme.onSurfaceVariant;
          final change=d==null?'—':(direction>0?'+':'')+
            _shortValue(d);
          return SizedBox(height:14,child:Align(alignment:Alignment.centerLeft,
            child:FittedBox(fit:BoxFit.scaleDown,alignment:Alignment.centerLeft,
              child:Row(mainAxisSize:MainAxisSize.min,children:[
                Text('Было '+_shortValue(old),
                  style:TextStyle(fontSize:10.5,
                    color:Theme.of(context).colorScheme.onSurfaceVariant)),
                const SizedBox(width:6),
                Text('Δ '+change,
                  style:TextStyle(fontSize:10.5,fontWeight:FontWeight.w700,
                    color:color))
              ]))));
        }));
  }
"""
needle='  Widget _number(String label,TextEditingController c,String unit,{bool integer=false,bool enabled=true})=>TextFormField('
s=one(s,needle,header+"\n"+needle.replace('=>TextFormField(','=>Column(crossAxisAlignment:CrossAxisAlignment.start,children:[TextFormField('),
      'comparison helper and field wrapper')
start=s.index('  Widget _number(String label,')
end=s.index('  Widget _text(',start)
piece=s[start:end]
piece=one(piece,'    });',
  '    }),_previousDelta(c,enabled:enabled)]);','comparison under field')
s=s[:start]+piece+s[end:]
p.write_text(s,encoding='utf-8')

chat=Path('lib/features/chat/promysel_chat_screen.dart')
c=chat.read_text(encoding='utf-8')
old="""child:ClipRRect(borderRadius:BorderRadius.circular(8),child:Image.network('${item['url']??''}',
                  width:((m['attachments'] as List?)??[]).length==1?250:126,height:((m['attachments'] as List?)??[]).length==1?190:112,
                  cacheWidth:500,cacheHeight:380,filterQuality:FilterQuality.low,fit:BoxFit.contain,errorBuilder:(_,__,___)=>const SizedBox(width:126,height:112,child:Icon(Icons.broken_image_outlined))))),"""
new="""child:ClipRRect(borderRadius:BorderRadius.circular(8),
                  child:ConstrainedBox(constraints:BoxConstraints(
                    maxWidth:((m['attachments'] as List?)??[]).length==1?250:126,
                    maxHeight:340),
                    child:Image.network('${item['url']??''}',cacheWidth:500,
                      filterQuality:FilterQuality.low,fit:BoxFit.contain,
                      errorBuilder:(_,__,___)=>const SizedBox(width:126,height:112,
                        child:Icon(Icons.broken_image_outlined)))))),"""
c=one(c,old,new,'photo album preserves intrinsic aspect')
old="""child:ClipRRect(borderRadius:BorderRadius.circular(10),child:Image.network(url,width:250,height:180,cacheWidth:500,cacheHeight:360,filterQuality:FilterQuality.low,fit:BoxFit.contain,errorBuilder:(_,__,___)=>const Text('Не удалось загрузить фото')))),"""
new="""child:ClipRRect(borderRadius:BorderRadius.circular(10),
             child:ConstrainedBox(constraints:const BoxConstraints(
               maxWidth:250,maxHeight:340),
               child:Image.network(url,cacheWidth:500,
                 filterQuality:FilterQuality.low,fit:BoxFit.contain,
                 errorBuilder:(_,__,___)=>const Text('Не удалось загрузить фото'))))),"""
c=one(c,old,new,'single photo preserves intrinsic aspect')
chat.write_text(c,encoding='utf-8')
print('PASS v2.28: compact last measurement/delta and intrinsic-aspect chat images')
