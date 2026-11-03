"""Install custom Android MainActivity and request notification permission."""
from pathlib import Path

r=Path.cwd()
source=Path(__file__).with_name('PromyselBadgeMainActivity.kt')
assert source.exists()
target=r/'android/app/src/main/kotlin/ru/promysel/promysel/MainActivity.kt'
assert target.parent.is_dir(),'Flutter Android platform missing'
target.write_text(source.read_text(encoding='utf-8'),encoding='utf-8')

manifest=r/'android/app/src/main/AndroidManifest.xml'
s=manifest.read_text(encoding='utf-8')
assert '<manifest' in s
if 'android.permission.POST_NOTIFICATIONS' not in s:
    s=s.replace('<manifest', '<manifest', 1)
    head=s.index('>',s.index('<manifest'))+1
    s=s[:head]+'\n    <uses-permission android:name="android.permission.POST_NOTIFICATIONS" />'+s[head:]
manifest.write_text(s,encoding='utf-8')
assert 'android.permission.POST_NOTIFICATIONS' in manifest.read_text()
assert 'requestPermissions' in target.read_text()
print('PASS: Android task launcher badge and notification permission')
