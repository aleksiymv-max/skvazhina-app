from pathlib import Path
import re
r=Path.cwd()
p=r/'lib/features/organization/profile_screen.dart'
s=p.read_text()

# Remove biometric dependency/state regardless of formatting.
s=re.sub(r"^.*local_auth.*\n?",'',s,flags=re.M)
s=re.sub(r"\s*final\s+auth\s*=\s*LocalAuthentication\(\)\s*;",'',s)

# Balanced method removal supports arbitrary whitespace between name and parentheses.
def remove_named_method(src,name):
    m=re.search(r'(?:Future<[^>]+>|Future|void)\s+'+re.escape(name)+r'\s*\(',src)
    if not m:return src
    i=m.start();b=src.find('{',m.end())
    if b<0:return src
    depth=0;j=b;quote=None;esc=False
    while j<len(src):
        c=src[j]
        if quote:
            if esc:esc=False
            elif c=='\\':esc=True
            elif c==quote:quote=None
        else:
            if c in "'\"":quote=c
            elif c=='{':depth+=1
            elif c=='}':
                depth-=1
                if depth==0:return src[:i]+src[j+1:]
        j+=1
    raise RuntimeError('Unbalanced method '+name)

# Old PIN/biometric implementations must be physically absent.
for name in ('_setPin','_bioLogin','_biometricLogin','_checkBiometrics','_testBiometrics','_bio'):
    while re.search(r'(?:Future<[^>]+>|Future|void)\s+'+re.escape(name)+r'\s*\(',s):s=remove_named_method(s,name)

# Remove complete ListTile/Card/SwitchListTile widgets containing PIN/biometric text/callback.
def remove_call_containing(src,call,needles):
    pos=0;needle=call+'('
    while True:
        i=src.find(needle,pos)
        if i<0:return src
        par=src.find('(',i);depth=0;j=par;quote=None;esc=False
        while j<len(src):
            c=src[j]
            if quote:
                if esc:esc=False
                elif c=='\\':esc=True
                elif c==quote:quote=None
            else:
                if c in "'\"":quote=c
                elif c=='(':depth+=1
                elif c==')':
                    depth-=1
                    if depth==0:
                        end=j+1
                        while end<len(src) and src[end] in ' \t':end+=1
                        if end<len(src) and src[end]==',':end+=1
                        block=src[i:end]
                        if any(n.lower() in block.lower() for n in needles):
                            src=src[:i]+src[end:];pos=max(0,i-1);break
                        pos=end;break
            j+=1
        else:return src

needles=['_setPin','PIN-код','PIN код','биометр','fingerprint','LocalAuthentication']
for call in ('ListTile','SwitchListTile','Card'):
    s=remove_call_containing(s,call,needles)

# Remove any residual standalone statements/lines from old quick-auth implementation.
for pat in (r'^.*quick_pin.*\n?',r'^.*quick_user.*\n?',r'^.*Проверить биометрию.*\n?',r'^.*Настроить PIN-код.*\n?',r'^.*_setPin.*\n?',r'^.*LocalAuthentication.*\n?'):
    s=re.sub(pat,'',s,flags=re.M)

# Deterministically replace password method with server-backed old/new/confirm dialog.
s=remove_named_method(s,'_changePassword')
class_end=s.rfind('}')
assert class_end>=0
method=r'''  Future<void> _changePassword() async {
    final oldPassword=TextEditingController();
    final newPassword=TextEditingController();
    final confirmPassword=TextEditingController();
    bool showOld=false,showNew=false,showConfirm=false;
    await showDialog<void>(context:context,builder:(dialogContext)=>StatefulBuilder(builder:(dialogContext,setDialog)=>AlertDialog(
      title:const Text('Изменить пароль'),
      content:Column(mainAxisSize:MainAxisSize.min,children:[
        TextField(controller:oldPassword,obscureText:!showOld,decoration:InputDecoration(labelText:'Текущий пароль',suffixIcon:IconButton(onPressed:()=>setDialog(()=>showOld=!showOld),icon:Icon(showOld?Icons.visibility_off:Icons.visibility)))),
        const SizedBox(height:10),
        TextField(controller:newPassword,obscureText:!showNew,decoration:InputDecoration(labelText:'Новый пароль',suffixIcon:IconButton(onPressed:()=>setDialog(()=>showNew=!showNew),icon:Icon(showNew?Icons.visibility_off:Icons.visibility)))),
        const SizedBox(height:10),
        TextField(controller:confirmPassword,obscureText:!showConfirm,decoration:InputDecoration(labelText:'Подтвердите новый пароль',suffixIcon:IconButton(onPressed:()=>setDialog(()=>showConfirm=!showConfirm),icon:Icon(showConfirm?Icons.visibility_off:Icons.visibility)))),
      ]),
      actions:[TextButton(onPressed:()=>Navigator.pop(dialogContext),child:const Text('Отмена')),FilledButton(onPressed:()async{
        if(newPassword.text!=confirmPassword.text){ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Пароли не совпадают')));return;}
        try{await SessionService.instance.changePassword(oldPassword.text,newPassword.text);if(dialogContext.mounted)Navigator.pop(dialogContext);if(mounted)ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Пароль изменён')));}
        catch(e){if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(e.toString())));}
      },child:const Text('Сохранить'))]
    )));
  }
'''
s=s[:class_end]+method+s[class_end:]
p.write_text(s)

# Remove package dependency too.
pub=r/'pubspec.yaml';q=pub.read_text();q=re.sub(r'^\s*local_auth:.*\n','',q,flags=re.M);pub.write_text(q)

# Final functional gates inspect the produced Dart, not patch-script text.
profile=p.read_text();login=(r/'lib/features/auth/login_screen.dart').read_text();pubtext=pub.read_text()
forbidden=['_setPin','quick_pin','Проверить биометрию','Настроить PIN-код','LocalAuthentication','local_auth:']
residual=[x for x in forbidden if x in profile+login+pubtext]
checks={
 'pin_bio_physically_absent':not residual,
 'password_old':"Текущий пароль" in profile,
 'password_confirm':"Подтвердите новый пароль" in profile,
 'password_match_guard':"newPassword.text!=confirmPassword.text" in profile,
 'password_server_call':"SessionService.instance.changePassword(oldPassword.text,newPassword.text)" in profile,
 'password_visibility':profile.count('Icons.visibility')>=6,
 'field_visible':"fieldName(SessionService.instance.currentFieldId!)" in profile,
}
print('V161 RESIDUAL',residual,flush=True);print('V161 FINAL PROFILE GATES',checks,flush=True)
bad=[k for k,v in checks.items() if not v]
assert not bad,'v1.61 final profile gate failed: '+', '.join(bad)
print('v1.61 deterministic profile auth cleanup passed',flush=True)
