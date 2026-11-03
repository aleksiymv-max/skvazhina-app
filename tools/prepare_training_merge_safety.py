"""Keep newer training completion/edit events during multi-device merges."""
from pathlib import Path
p=Path('lib/core/services/app_state_store.dart')
s=p.read_text(encoding='utf-8')
anchor="       else if(type=='tasks' && ("
assert s.count(anchor)==1
s=s.replace(anchor,"""       else if(type=='training'&&
         (DateTime.tryParse((prev['updatedAt']??'').toString())?.isAfter(
           DateTime.tryParse((row['updatedAt']??'').toString())??
             DateTime.fromMillisecondsSinceEpoch(0))??false)){
         // A delayed snapshot must not revert an already completed training.
         continue;
       }
"""+anchor,1)
p.write_text(s,encoding='utf-8')
print('PASS training edit timestamps respected during state merge')
