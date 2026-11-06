#!/usr/bin/env python3
"""v2.21 independent issues + About-to-Menu routing regression contract."""
from pathlib import Path

root=Path('lib')
walk=(root/'features/walk/walk_start_screen.dart').read_text(encoding='utf-8')
form=(root/'features/problems/field_problem_form_screen.dart').read_text(encoding='utf-8')
home=(root/'features/home/home_screen.dart').read_text(encoding='utf-8')
store=(root/'core/services/field_problem_report_store.dart').read_text(encoding='utf-8')
about=(root/'features/menu/about_screen.dart').read_text(encoding='utf-8')
menu=(root/'features/menu/menu_screen.dart').read_text(encoding='utf-8')
app=(root/'app/app.dart').read_text(encoding='utf-8')
sql=(Path(__file__).resolve().parents[1]/
     'supabase/migrations/20261106094500_field_problem_reports_v221.sql').read_text(encoding='utf-8')

checks={
 'button before areas':walk.index("'Подать заявку'")<walk.index("'Участки добычи'"),
 'new form is separate from rounds':'FieldProblemFormScreen' in walk and
      'FieldProblemReportStore.instance.create(' in form and
      'MeasurementRepository' not in form,
 'required area/pad':"validator:(v)=>v==null?'Выберите участок'" in form and
      "validator:(v)=>v==null?'Выберите куст'" in form,
 'well optional':"Весь куст — без скважины" in form and
      "wellId:well?.id,wellNumber:well?.number" in form,
 'description required':"if(text.isEmpty)return 'Опишите проблему'" in form and
      'maxLength:2000' in form,
 'main problem count and list':'FieldProblemReportStore.instance.openCount' in home and
      'FieldProblemReportStore.instance.openReports' in home and
      '_standaloneProblemCard(report)' in home,
 'author and creation time':"report.authorName" in home and
      "_problemDate(report.createdAt)" in home,
 'resolution role restricted':'canResolveProblems' in home and
      'FieldProblemReportStore.instance.resolve(report.id)' in home,
 'local outbox before network':store.index("await _persist();}catch(_)")<
      store.index("unawaited(refresh(force:true))"),
 'idempotency and no blind retries':'resolution=ignore-duplicates' in store and
      "for(final m in _pending.values.toList())" in store and
      "return; // Keep pending." in store,
 'auth and field scope':'RegistrationService.publishableKey' in store and
      'SessionService.instance.ensureFreshToken()' in store and
      "field_id':'eq.$fid" in store and
      "m.fieldId==fid" in store,
 'no fake well measurement':'insertMeasurement' not in store and
      'saveWalk' not in form,
 'persistent dedicated storage':"promysel_field_problems_v221_" in store and
      "'pending':_pending.values" in store,
 'About route belongs to Menu':"GoRoute(path:'about'" in app and
      "onTap:()=>context.push('/menu/about')" in menu,
 'Menu tab returns to root':"if(index==4){context.go('/menu');return;}" in app and
      "onPressed:()=>context.go('/menu')" in about,
 'manual explains standalone applications':"Подать заявку без обхода скважины" in about and
      "скважину выбирать не требуется" in about,
 'diagnostic exposes pending problem reports':'FieldProblemReportStore.instance.pendingCount' in about,
 'database field-scoped RLS':'ENABLE ROW LEVEL SECURITY' in sql and
      'app_private.is_member(field_id)' in sql and
      "author_id=(select auth.uid())" in sql,
 'reporter identity server-verified':'SELECT m.display_name INTO real_name' in sql and
      'NEW.author_name:=real_name;' in sql,
 'no database wipe':not any(x in sql.lower() for x in
      ['drop table','truncate table','delete from public.']),
 'current version displayed':'Версия v2.21' in about
}
for label,ok in checks.items():print(('PASS ' if ok else 'FAIL ')+label)
assert all(checks.values()),'v2.21 standalone issue regression failed'
