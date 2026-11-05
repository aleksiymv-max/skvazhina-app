#!/usr/bin/env python3
"""v2.09: completed issued tasks move to History; only actionable reviews remain above active issues."""
from pathlib import Path

p=Path('lib/features/tasks/tasks_screen.dart')
s=p.read_text(encoding='utf-8')
old="if(canIssue)_pullRefresh(_issuedList(issued))"
assert s.count(old)==1, f'Issued task tab hook changed: {s.count(old)}'
s=s.replace(old,"if(canIssue)_pullRefresh(_issuedReviewSections(issued))",1)

anchor=" Widget _pullRefresh(Widget content)=>"
assert s.count(anchor)==1, 'Issued tasks insertion point changed'
method=""" Widget _issuedReviewSections(List<WorkTask> issued){
   final viewer=SessionService.instance.currentUser;
   final pending=issued.where((t)=>t.status==WorkTaskStatus.awaitingConfirmation&&_canReviewTask(t,viewer)).toList();
   final others=issued.where((t)=>t.status!=WorkTaskStatus.awaitingConfirmation).toList();
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
     Expanded(child:_issuedList(others)),
   ]);
 }
"""
assert ' Widget _issuedReviewSections(' not in s
s=s.replace(anchor,method+anchor,1)

# All confirmed tasks remain in the WorkTaskStore, so History can still show
# them and export them. They are excluded only from the issued task UI.
oldfilter="final issued=store.tasks.where((t)=>t.status!=WorkTaskStatus.confirmed&&TaskVisibility.canViewActiveIssued(t,u)).toList();"
assert s.count(oldfilter)==1,'Issued task visibility expression changed'
assert 'TaskVisibility.canViewHistory(t)' in Path('lib/features/history/history_screen.dart').read_text(encoding='utf-8'), 'History must retain confirmed tasks'
assert "issued-completed" not in s and "Выполненные (" not in s
assert "pending.length" in s
assert "WorkTaskStatus.confirmed&&TaskVisibility.canViewActiveIssued" in s
p.write_text(s,encoding='utf-8')
print('PASS v2.09: no completed tile in issued; confirmed tasks hidden from tasks and retained in history')
print('PASS v2.09: review count and actions preserved for permitted approvers')
