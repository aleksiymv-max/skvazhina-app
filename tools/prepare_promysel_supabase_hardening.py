from pathlib import Path

# Runs after prepare_promysel_supabase_adapter.py.
# Prevents cross-field sync cursors and preserves locally configured well parameters.
root=Path.cwd()
sync=root/'lib/core/services/sync_service.dart'
s=sync.read_text()
old="String _deviceId='',_cursor='0';"
new="String _deviceId='',_cursor='0',_cursorField='';"
assert old in s, "SyncService cursor state changed"
s=s.replace(old,new,1)
old="_cursor=prefs.getString('sync_cursor')??'0';if(_cursor.trim().isEmpty)_cursor='0';"
assert old in s, "Global sync cursor anchor changed"
s=s.replace(old,"_cursor='0';_cursorField='';",1)
old="    final fieldId=SessionService.instance.currentFieldId;if(fieldId==null||fieldId.isEmpty)return;final res=await http.get"
new="""    final fieldId=SessionService.instance.currentFieldId;if(fieldId==null||fieldId.isEmpty)return;
    if(_cursorField!=fieldId){
      final prefs=await SharedPreferences.getInstance();
      _cursor=prefs.getString('sync_cursor_${fieldId}')??'0';
      if(_cursor.trim().isEmpty)_cursor='0';
      _cursorField=fieldId;
    }
    final res=await http.get"""
assert old in s, "Sync pull cursor anchor changed"
s=s.replace(old,new,1)
old="prefs.setString('sync_cursor',_cursor)"
assert old in s, "Global cursor persistence anchor changed"
s=s.replace(old,"prefs.setString('sync_cursor_${fieldId}',_cursor)",1)
sync.write_text(s)

cfg=root/'lib/core/network/api_config.dart'
s=cfg.read_text()
old="defaultValue: 'http://10.0.2.2:8000'"
assert old in s, "Default API URL anchor changed"
s=s.replace(old,"defaultValue: 'https://xptmcufhuvtcunqzlsme.supabase.co/functions/v1/promysel-compat'",1)
cfg.write_text(s)

pad=root/'lib/features/pads/pad_screen.dart'
s=pad.read_text()
old="if (SessionService.instance.token != null) {"
assert old in s, "Pad network fallback anchor changed"
s=s.replace(old,"if (SessionService.instance.token != null && wells.isEmpty) {",1)
pad.write_text(s)

assert "sync_cursor_${fieldId}" in sync.read_text()
assert "&& wells.isEmpty" in pad.read_text()
assert "promysel-compat" in cfg.read_text()
print("Promysel Supabase hardening: isolated field cursors, correct API base, local well parameter preservation")
