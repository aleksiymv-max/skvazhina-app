#!/usr/bin/env python3
"""v2.30: deemphasize historical comparisons without changing entered values or units."""
from pathlib import Path
p=Path('lib/features/wells/well_screen.dart')
text=p.read_text(encoding='utf-8')
start=text.index('  Widget _comparisonSuffix(')
end=text.index('  Widget _number(',start)
block=text[start:end]
assert block.count('const size=17.0;')==1
block=block.replace('const size=17.0; // The same font size as the editable numeric value.',
'''const size=11.5; // Historical context, visually subordinate to 17px input.
    const unitSize=17.0; // Keep units prominent and distinct.''')
assert "color:muted.withValues(alpha:.58)" in block
block=block.replace('color:muted.withValues(alpha:.58)','color:muted.withValues(alpha:.46)')
assert 'color:highlight,' in block
block=block.replace('color:highlight,','color:highlight.withValues(alpha:.58),')
assert 'fontWeight:FontWeight.w600' in block
block=block.replace('fontWeight:FontWeight.w600','fontWeight:FontWeight.w500')
needle='Text(unit,maxLines:1,softWrap:false,\n                style:TextStyle(fontSize:size,color:muted))'
assert needle in block
block=block.replace(needle,'Text(unit,maxLines:1,softWrap:false,\n                style:TextStyle(fontSize:unitSize,color:muted))')
text=text[:start]+block+text[end:]
p.write_text(text,encoding='utf-8')
print('PASS v2.30: previous reading 11.5pt muted, delta subdued, entered value and unit 17pt, edit focus unchanged')
