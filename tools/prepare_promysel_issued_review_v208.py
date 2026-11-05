#!/usr/bin/env python3
"""v2.08 issued task review: collapsible pending approval section and completed section."""
from pathlib import Path
p=Path('lib/features/tasks/tasks_screen.dart')
s=p.read_text(encoding='utf-8')
old="if(canIssue)_pullRefresh(_issuedList(issued))"
assert s.count(old)==1, f'issued tab anchor changed: {s.count(old)}'
s=s.replace(old,"if(canIssue)_pullRefresh(_issuedReviewSections(issued))",1)
anchor=" Widget _pullRefresh(Widget content)=>"
assert s.count(anchor)==1, 'task screen method anchor changed'
new=""" Widget _issuedReviewSections(List<WorkTask> issued){
   final pending=issued.where((t)=>t.status==WorkTaskStatus.awaitingConfirmation&&_canReviewTask(t,SessionService.instance.currentUser)).toList();
   final completed=issued.where((t)=>t.status==WorkTaskStatus.confirmed).toList();
   final others=issued.where((t)=>t.status!=WorkTaskStatus.confirmed&&(t.status!=WorkTaskStatus.awaitingConfirmation||!_canReviewTask(t,SessionService.instance.currentUser))).toList();
   return Column(children:[
     Card(child:ExpansionTile(
       key:const PageStorageKey('issued-pending-review'),
       initiallyExpanded:pending.isNotEmpty,
       title:const Text('Требуют подтверждения'),
       subtitle:Text('Заданий: ${pending.length}'),
       trailing:Row(mainAxisSize:MainAxisSize.min,children:[
         if(pending.isNotEmpty)CircleAvatar(radius:13,child:Text('${pending.length}',style:const TextStyle(fontSize:12))),
         const Icon(Icons.expand_more),
       ]),
       children:[
         if(pending.isEmpty)const Padding(padding:EdgeInsets.all(16),child:Text('Нет заданий на подтверждение')),
         if(pending.isNotEmpty)SizedBox(height:(pending.length*250.0).clamp(160.0,480.0).toDouble(),child:_issuedList(pending)),
       ],
     )),
     Card(child:ExpansionTile(
       key:const PageStorageKey('issued-completed'),
       title:Text('Выполненные (${completed.length})'),
       children:[
         if(completed.isEmpty)const Padding(padding:EdgeInsets.all(16),child:Text('Нет подтверждённых заданий')),
         if(completed.isNotEmpty)SizedBox(height:(completed.length*250.0).clamp(160.0,480.0),child:_issuedList(completed)),
       ],
     )),
     Expanded(child:_issuedList(others)),
   ]);
 }
"""
assert ' Widget _issuedReviewSections(' not in s
s=s.replace(anchor,new+anchor,1)
# Existing issued filter used to hide confirmed tasks; include them for completed section.
oldfilter="final issued=store.tasks.where((t)=>t.status!=WorkTaskStatus.confirmed&&TaskVisibility.canViewActiveIssued(t,u)).toList();"
assert s.count(oldfilter)==1, 'issued filter changed; inspect before applying'
s=s.replace(oldfilter,"final issued=store.tasks.where((t)=>TaskVisibility.canViewActiveIssued(t,u)).toList();",1)
p.write_text(s,encoding='utf-8')
print('PASS: pending approval count, in-place expandable list, completed section')
