from pathlib import Path
r=Path.cwd()

# v1.53: guarantee persisted annulus-pressure data is loaded before history/export reads it.
p=r/'lib/core/services/annulus_pressure_store.dart'; s=p.read_text()
old="class AnnulusPressureStore extends ChangeNotifier{AnnulusPressureStore._(){_load();}static final instance=AnnulusPressureStore._();final List<AnnulusPressureEntry> entries=[];Future<void> _load()async{final p=await SharedPreferences.getInstance();"
new="class AnnulusPressureStore extends ChangeNotifier{AnnulusPressureStore._(){_loadFuture=_load();}static final instance=AnnulusPressureStore._();final List<AnnulusPressureEntry> entries=[];late final Future<void> _loadFuture;Future<void> ensureLoaded()=>_loadFuture;Future<void> _load()async{final p=await SharedPreferences.getInstance();"
if old not in s: raise SystemExit('annulus store constructor pattern not found')
s=s.replace(old,new,1); p.write_text(s)

p=r/'lib/features/history/history_screen.dart'; s=p.read_text()
old="if(action=='annulus'){final f=await ExportService.createAnnulusJournalXlsx(entries:AnnulusPressureStore.instance.history());await ExportService.shareXlsx(f);return;}"
new="if(action=='annulus'){await AnnulusPressureStore.instance.ensureLoaded();final entries=AnnulusPressureStore.instance.history();if(entries.isEmpty){if(mounted)ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Нет сохранённых показаний межколонных давлений для выгрузки.')));return;}final f=await ExportService.createAnnulusJournalXlsx(entries:entries);await ExportService.shareXlsx(f);return;}"
if old not in s: raise SystemExit('annulus export dispatch pattern not found')
s=s.replace(old,new,1); p.write_text(s)

# Regression gates: export must wait for persistent store, and agreed area-sheet exporter remains intact.
store=(r/'lib/core/services/annulus_pressure_store.dart').read_text()
hist=(r/'lib/features/history/history_screen.dart').read_text()
exp=(r/'lib/core/services/export_service.dart').read_text()
assert "Future<void> ensureLoaded()=>_loadFuture" in store
assert "await AnnulusPressureStore.instance.ensureLoaded()" in hist
assert "final entries=AnnulusPressureStore.instance.history()" in hist
assert "if(entries.isEmpty)" in hist
assert "final areas=<String,List<AnnulusPressureEntry>>{}" in exp
assert "areas.putIfAbsent" in exp
assert "МКД 178×245, МПа" in exp and "МКД 245×324, МПа" in exp
print("v1.53 persisted annulus export loading gates passed")
