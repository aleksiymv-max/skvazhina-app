#!/usr/bin/env python3
"""v2.30 source regressions: dispatcher access, button order, durable remote request ledger."""
from pathlib import Path
home=Path('lib/features/home/home_screen.dart').read_text()
role=Path('lib/core/models/user.dart').read_text()
store=Path('lib/core/services/problem_application_store.dart').read_text()
well=Path('lib/features/wells/well_screen.dart').read_text()
part=home[home.index(' Future<void> _showProblems() async {'):home.index(' Widget _standaloneProblemCard(')]
detail=home[home.index(' Widget _standaloneProblemCard('):]
checks={
 'engineer dispatcher allowed':"role == UserRole.engineer && itrSubrole == ItrSubrole.dispatcher" in role,
 'ordinary operator excluded':"bool get canFileProblemApplication => role == UserRole.dispatcher" in role,
 'local key read for current field':"u+'_'+_field" in store,
 'server audit ledger REST present':'promysel_problem_dispatches' in store,
 'measurement stable sync id not local integer':"problemSyncIdentity(id)" in store and 'measurement:' in store,
 'offline queue persisted before upload':'await _persist();' in store and '_pending[key]=item;' in store,
 'read only own field':"'field_id':'eq.'+field" in store,
 'server reject is retained':"Отметка диспетчера ожидает отправки" in store,
 'timestamp above Resolve in legacy':part.index("if(application!=null)Padding(")<part.index("label:const Text('Решено')"),
 'dispatcher button below Resolve in legacy':part.index("label:const Text('Подать заявку')")>part.index("label:const Text('Решено')"),
 'timestamp above Resolve in standalone':detail.index("Заявка подана: ")<detail.index("label:const Text('Решено')"),
 'dispatcher button below Resolve in standalone':detail.index("label:const Text('Подать заявку')")>detail.index("label:const Text('Решено')"),
 'legacy local data array no longer in UI':"ProblemApplicationStore.instance.data[" not in home,
 'open modal updates on network completion':"AnimatedBuilder(animation:ProblemApplicationStore.instance" in part,
 'font reduced':"const size=11.5" in well,
 'unit and number remain full size':"const unitSize=17.0" in well and "style:const TextStyle(fontSize:17)" in well,
 'input still hit test transparent':'IgnorePointer(ignoring:true' in well,
}
for k,v in checks.items():print(('PASS ' if v else 'FAIL ')+k)
assert all(checks.values()),'v230 regression check failed'
