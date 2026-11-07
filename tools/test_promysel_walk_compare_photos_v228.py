#!/usr/bin/env python3
"""v2.28 source guards: compact per-well past reading and original aspect thumbnails."""
from pathlib import Path
p=Path('lib/features/wells/well_screen.dart').read_text(encoding='utf-8')
c=Path('lib/features/chat/promysel_chat_screen.dart').read_text(encoding='utf-8')
checks={
 'same pad and well one local record':"padId:widget.padId,wellId:widget.wellId,limit:1" in p,
 'previous reading top of walk':"children:[_previousHeader(),_statusSelector()" in p,
 'prior operator metadata':'last.operatorName?.trim()' in p,
 'prior measurement time':'_priorTime(last.measuredAt)' in p,
 'numeric comparison live only local':'ValueListenableBuilder<TextEditingValue>' in p,
 'negative deviation red':'direction<0?Colors.red.shade700' in p,
 'positive deviation green':'direction>0?Colors.green.shade700' in p,
 'previous and delta small':'_shortValue(old)' in p and "'Δ '+change" in p,
 'no extra requests on keystrokes':'_previousDelta(c,enabled:enabled)' in p,
 'comma decimal parser':'PromyselDecimalInput.parse(input.text)' in p,
 'disabled field comparison hidden':'if(!enabled||previous==null)' in p,
 'album aspect preserved':'maxWidth:((m[\'attachments\'] as List?)??[]).length==1?250:126' in c,
 'single image aspect preserved':'maxWidth:250,maxHeight:340' in c,
 'native aspect no forced image height':"Image.network(url,width:250,height:180" not in c and "cacheWidth:500,cacheHeight:380" not in c,
 'chat full view preserved':"InteractiveViewer(child:Image.network" in c
}
for key,ok in checks.items():print(('PASS' if ok else 'FAIL')+' '+key)
assert all(checks.values()),'v2.28 comparison/photo regression'
