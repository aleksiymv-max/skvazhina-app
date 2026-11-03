"""Task badge on bottom bar, supplied enhanced photo on login, round logo.
Runs after unified completion and notification patches. No production DB writes.
"""
from pathlib import Path
import base64,hashlib
r=Path.cwd()
rawfile=Path(__file__).with_name('promysel_login_background.b64')
assert rawfile.is_file(), 'Login background source missing'
raw=base64.b64decode(''.join(rawfile.read_text(encoding='ascii').split()),validate=True)
assert raw.startswith(b'RIFF') and raw[8:12]==b'WEBP', 'Invalid WebP background'
bg=r/'assets/login/promysel_background.webp'
bg.parent.mkdir(parents=True,exist_ok=True)
bg.write_bytes(raw)
print('PROMYSEL PHOTO',len(raw),hashlib.sha256(raw).hexdigest(),flush=True)

pub=r/'pubspec.yaml';s=pub.read_text()
anchor='    - assets/icon/app_icon.png'
assert s.count(anchor)==1
s=s.replace(anchor,anchor+'\n    - assets/login/promysel_background.webp',1)
pub.write_text(s)

login=r/'lib/features/auth/login_screen.dart';s=login.read_text()
a=s.index(' @override Widget build(BuildContext context)')
b=s.index(' Future<void> _login()',a)
body=s[a:b]
old="Image.asset('assets/icon/app_icon.png',width:104,height:104)"
assert body.count(old)==1
body=body.replace(old,"ClipOval(child:Image.asset('assets/icon/app_icon.png',width:104,height:104,fit:BoxFit.cover))",1)
old='return Scaffold(body:SafeArea('
assert body.count(old)==1
body=body.replace(old,"return Scaffold(body:Container(decoration:const BoxDecoration(image:DecorationImage(image:AssetImage('assets/login/promysel_background.webp'),fit:BoxFit.cover,colorFilter:ColorFilter.mode(Color(0x88FFFFFF),BlendMode.lighten))),child:SafeArea(",1)
closing=body.rfind(';')
assert closing>0 and body[:closing].rstrip().endswith(')'), 'Unknown login layout'
body=body[:closing].rstrip() + ')' + body[closing:]
s=s[:a]+body+s[b:]
login.write_text(s)

app=r/'lib/app/app.dart';s=app.read_text()
anchor="import '../core/models/user.dart';"
assert s.count(anchor)==1
s=s.replace(anchor,anchor+"\nimport '../core/services/notification_store.dart';",1)
a=s.index('class _MainShell extends StatelessWidget')
head,tail=s[:a],s[a:]
anchor='@override Widget build(BuildContext context)=>Scaffold('
assert tail.count(anchor)==1
tail=tail.replace(anchor,'@override Widget build(BuildContext context)=>ListenableBuilder(listenable:NotificationStore.instance,builder:(context,_)=>Scaffold(',1)
anchor='destinations:const ['
assert tail.count(anchor)==1
tail=tail.replace(anchor,'destinations:[',1)
old="NavigationDestination(icon:Icon(Icons.task_alt_outlined),selectedIcon:Icon(Icons.task_alt),label:'Задания')"
assert tail.count(old)==1
badge="""NavigationDestination(
 icon:Badge(isLabelVisible:NotificationStore.instance.unread(SessionService.instance.currentUser.id)>0,child:const Icon(Icons.task_alt_outlined)),
 selectedIcon:Badge(isLabelVisible:NotificationStore.instance.unread(SessionService.instance.currentUser.id)>0,child:const Icon(Icons.task_alt)),
 label:'Задания')"""
tail=tail.replace(old,badge,1)
k=tail.rfind(');')
assert k>=0
tail=tail[:k]+'));'+tail[k+2:]
app.write_text(head+tail)

checks={
 'user_photo_is_an_app_asset':bg.exists() and len(raw)>1000 and 'assets/login/promysel_background.webp' in pub.read_text(),
 'login_uses_photo':"AssetImage('assets/login/promysel_background.webp')" in login.read_text(),
 'logo_has_no_square_corners':'ClipOval(child:Image.asset' in login.read_text(),
 'bottom_task_badge':'NavigationDestination(\n icon:Badge(' in app.read_text() and 'NotificationStore.instance.unread' in app.read_text(),
 'bottom_updates_on_unread':'ListenableBuilder(listenable:NotificationStore.instance' in app.read_text(),
}
assert all(checks.values()),checks
print('PASS task badge and photographic login',checks,flush=True)
