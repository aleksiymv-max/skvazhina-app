#!/usr/bin/env python3
"""v2.06: decimal comma in EVERY measurement field, including both chokes."""
from pathlib import Path

def one(src, old, new, label):
    count=src.count(old)
    if count!=1:
        raise RuntimeError(f"{label}: expected 1 match, got {count}")
    return src.replace(old,new,1)

source=Path(__file__).with_name('promysel_decimal_input_v206.dart')
target=Path('lib/core/services/promysel_decimal_input.dart')
assert source.exists() and not target.exists(), 'decimal input module already installed'
target.write_text(source.read_text(encoding='utf-8'),encoding='utf-8')

p=Path('lib/features/wells/well_screen.dart')
s=p.read_text(encoding='utf-8')
s="import '../../core/services/promysel_decimal_input.dart';\n"+s
for name in ('Дроссель 1','Дроссель 2'):
    import re
    old=re.search(r"_number\('"+name+r"',(choke[12]),unitP\('choke','%'\),integer:true\)",s)
    if old is None:raise RuntimeError('Missing choke field '+name)
    s=s.replace(old.group(0),old.group(0).replace(',integer:true',''),1)
s=one(s,
 "  double? _d(TextEditingController c)=>double.tryParse(c.text.trim().replaceAll(',','.'));",
 "  double? _d(TextEditingController c)=>PromyselDecimalInput.parse(c.text);",
 'unified numeric parse')
old="Widget _number(String label,TextEditingController c,String unit,{bool integer=false,bool enabled=true})=>TextFormField(controller:c,enabled:enabled,keyboardType:TextInputType.numberWithOptions(decimal:!integer),decoration:InputDecoration(labelText:label,suffixText:unit,hintText:'Не измерено'),validator:(v){if(!enabled||v==null||v.trim().isEmpty)return null;final n=double.tryParse(v.replaceAll(',','.'));if(n==null||!n.isFinite||(integer&&n%1!=0)||n<0)return'Проверьте значение';return null;});"
new="""Widget _number(String label,TextEditingController c,String unit,{bool integer=false,bool enabled=true})=>TextFormField(
    controller:c,enabled:enabled,
    keyboardType:TextInputType.numberWithOptions(decimal:!integer),
    inputFormatters:[integer?PromyselDecimalInput.integer:PromyselDecimalInput.decimal],
    decoration:InputDecoration(labelText:label,suffixText:unit,hintText:'Не измерено',
      suffixIconConstraints:const BoxConstraints(minWidth:30,minHeight:34),
      suffixIcon:integer?null:IconButton(
        visualDensity:VisualDensity.compact,padding:EdgeInsets.zero,
        constraints:const BoxConstraints(minWidth:30,minHeight:34),
        tooltip:'Вставить запятую',onPressed:enabled?
          ()=>PromyselDecimalInput.insertComma(c):null,
        icon:const Text(',',style:TextStyle(fontSize:23,fontWeight:FontWeight.bold)),
      ),
    ),
    validator:(v){
      if(!enabled||v==null||v.trim().isEmpty)return null;
      final n=PromyselDecimalInput.parse(v);
      if(n==null||!n.isFinite||(integer&&n%1!=0)||n<0)return'Проверьте значение';
      return null;
    });"""
s=one(s,old,new,'all numeric well input fields')
p.write_text(s,encoding='utf-8')

for path in ['lib/features/walk/pad_walk_card_screen.dart',
             'lib/features/history/history_screen.dart']:
    p=Path(path);s=p.read_text(encoding='utf-8')
    s="import '../../core/services/promysel_decimal_input.dart';\n"+s
    old='keyboardType:const TextInputType.numberWithOptions(decimal:true),'
    if s.count(old)<2:raise RuntimeError('Annulus numeric inputs missing in '+path)
    s=s.replace(old,old+'inputFormatters:[PromyselDecimalInput.decimal],')
    # Keep the existing UI; both dot and comma are now accepted for pasted text
    # and locale-specific decimal keyboards.
    p.write_text(s,encoding='utf-8')

print('PASS v2.06 comma and dot in well parameters and annulus pressure; PKV integers retained')
