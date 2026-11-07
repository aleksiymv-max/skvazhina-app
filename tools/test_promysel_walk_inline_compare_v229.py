#!/usr/bin/env python3
"""Regression assertions: comparison inside editable numeric cell, no overlap row."""
from pathlib import Path
s=Path('lib/features/wells/well_screen.dart').read_text()
checks={
 'comparison embedded as suffix':"suffix:_comparisonSuffix(c,unit,enabled:enabled,fieldWidth:bounds.maxWidth)" in s,
 'visual overlay is pointer-transparent':"IgnorePointer(ignoring:true" in s,
 'all number input stays TextFormField':"Widget _number(String label,TextEditingController c,String unit,{bool integer=false,bool enabled=true})=>LayoutBuilder(builder:(context,bounds)=>TextFormField(" in s,
 'measurement header unchanged':"_previousHeader()" in s,
 'old comparison removed from under input':"_previousDelta(" not in s,
 'field and suffix same text size':"style:const TextStyle(fontSize:17)" in s and "const size=17.0" in s,
 'signed difference preserved':"direction<0?Colors.red.shade700" in s and "direction>0?Colors.green.shade700" in s,
 'comma parser preserved':"PromyselDecimalInput.parse(input.text)" in s,
 'unit remains inside interactive cell':"Text(unit,maxLines:1" in s,
 'fits narrow numeric inputs':"BoxConstraints(maxWidth:fieldWidth*.64)" in s and "BoxFit.scaleDown" in s
}
for name,ok in checks.items():print(('PASS' if ok else 'FAIL')+' '+name)
assert all(checks.values()),'v229 regression'
