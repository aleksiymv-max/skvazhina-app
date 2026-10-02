from pathlib import Path
import re
r=Path.cwd()
p=r/'lib/features/organization/profile_screen.dart'
s=p.read_text()

# Remove biometric dependency/state regardless of formatting.
s=re.sub(r"^.*local_auth.*\n?",'',s,flags=re.M)
s=re.sub(r"\s*final\s+auth\s*=\s*LocalAuthentication\(\)\s*;",'',s)

# Remove complete methods by balanced braces, not regex.
def remove_method(src, marker):
    i=src.find(marker)
    if i<0:return src
    b=src.find('{',i)
    if b<0:return src
    depth=0;j=b
    while j<len(src):
        if src[j]=='{':depth+=1
        elif src[j]=='}':
            depth-=1
            if depth==0:
                return src[:i]+src[j+1:]
        j+=1
    raise RuntimeError('Unbalanced method '+marker)

# Old PIN implementation must be physically absent.
s=remove_method(s,'Future<void> _setPin(')
s=remove_method(s,'Future<void> _bio')
s=remove_method(s,'Future<void> _biometric')

# Remove UI statements containing PIN/biometric callbacks/text using balanced ListTile parentheses.
def remove_listtile_containing(src, needles):
    pos=0
    while True:
        i=src.find('ListTile(',pos)
        if i<0:return src
        depth=0;j=i+len('ListTile')
        quote=None;esc=False
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

s=remove_listtile_containing(s,['_setPin','PIN-код','биометр','fingerprint','LocalAuthentication'])
# Remove obsolete quick-auth storage operations but keep photo secure storage.
s=re.sub(r"[^;\n]*quick_pin[^;\n]*;",'',s)
s=re.sub(r"[^;\n]*quick_user[^;\n]*;",'',s)

# Deterministically replace password method with server-backed old/new/confirm dialog.
s=remove_method(s,'Future<void> _changePassword(')
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
