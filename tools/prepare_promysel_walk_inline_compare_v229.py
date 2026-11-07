#!/usr/bin/env python3
"""v2.29: make previous reading/delta a transparent, non-interactive suffix inside the numeric field."""
from pathlib import Path

p=Path("lib/features/wells/well_screen.dart")
s=p.read_text(encoding="utf-8")
old_start=s.index("  Widget _previousDelta(TextEditingController c,{required bool enabled}){")
old_end=s.index("  Widget _number(String label,",old_start)
inline="""  // Visual-only text inside InputDecoration: the entire cell stays a single
  // TextFormField hit target. No extra row under the next parameter's label.
  Widget _comparisonSuffix(TextEditingController controller,String unit,
      {required bool enabled,required double fieldWidth}){
    final previous=_previousMeasurement;
    final old=previous==null||!enabled?null:_priorNumber(controller,previous);
    final hasOld=old!=null&&old.isFinite;
    final muted=Theme.of(context).colorScheme.onSurfaceVariant;
    const size=17.0; // The same font size as the editable numeric value.
    return IgnorePointer(ignoring:true,child:
      ValueListenableBuilder<TextEditingValue>(
        valueListenable:controller,builder:(context,input,_){
          final now=PromyselDecimalInput.parse(input.text);
          final delta=!hasOld||now==null||!now.isFinite?
            null:now-old;
          final direction=delta==null||delta.abs()<0.005?
            0:(delta>0?1:-1);
          final highlight=direction>0?Colors.green.shade700:
            direction<0?Colors.red.shade700:muted;
          final change=delta==null?'—':
            (direction>0?'+':'')+_shortValue(delta);
          return ConstrainedBox(constraints:BoxConstraints(maxWidth:fieldWidth*.64),
            child:FittedBox(fit:BoxFit.scaleDown,alignment:Alignment.centerRight,
              child:Row(mainAxisSize:MainAxisSize.min,
            crossAxisAlignment:CrossAxisAlignment.baseline,
            textBaseline:TextBaseline.alphabetic,children:[
              if(hasOld)...[
                Text('Было '+_shortValue(old),
                  maxLines:1,softWrap:false,
                  style:TextStyle(fontSize:size,color:muted.withValues(alpha:.58))),
                const SizedBox(width:8),
                Text('Δ '+change,maxLines:1,softWrap:false,
                  style:TextStyle(fontSize:size,color:highlight,
                    fontWeight:FontWeight.w600)),
                const SizedBox(width:13),
              ],
              Text(unit,maxLines:1,softWrap:false,
                style:TextStyle(fontSize:size,color:muted)),
            ])));
        }));
  }

"""
s=s[:old_start]+inline+s[old_end:]
start=s.index("  Widget _number(String label,")
end=s.index("  Widget _text(",start)
block=s[start:end]
old="""=>Column(crossAxisAlignment:CrossAxisAlignment.start,children:[TextFormField("""
if block.count(old)!=1:raise AssertionError("number field wrapper mismatch")
block=block.replace(old,"=>LayoutBuilder(builder:(context,bounds)=>TextFormField(",1)
old="    controller:c,enabled:enabled,"
if block.count(old)!=1:raise AssertionError("number controller mismatch")
block=block.replace(old,"    controller:c,enabled:enabled,\n    style:const TextStyle(fontSize:17),",1)
old="decoration:InputDecoration(labelText:label,suffixText:unit,hintText:'Не измерено',"
if block.count(old)!=1:raise AssertionError("suffixText/unit mismatch")
block=block.replace(old,
 "decoration:InputDecoration(labelText:label,\n"
 "      suffix:_comparisonSuffix(c,unit,enabled:enabled,fieldWidth:bounds.maxWidth),\n"
 "      hintText:'Не измерено',",1)
old="    }),_previousDelta(c,enabled:enabled)]);"
if block.count(old)!=1:raise AssertionError("old separate comparison row mismatch")
block=block.replace(old,"    }));",1)
s=s[:start]+block+s[end:]
assert "_previousDelta(" not in s
assert "suffix:_comparisonSuffix(c,unit,enabled:enabled,fieldWidth:bounds.maxWidth)" in s
assert "IgnorePointer(ignoring:true" in s
p.write_text(s,encoding="utf-8")
print("PASS v2.29: inline baseline suffix / input remains tappable / no separate delta row")
