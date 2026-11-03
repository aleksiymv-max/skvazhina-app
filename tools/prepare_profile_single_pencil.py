"""Single edit-pencil control with edit/remove actions in a sheet."""
from pathlib import Path
p=Path('lib/features/organization/profile_screen.dart')
s=p.read_text(encoding='utf-8')
start=s.index('  Positioned(right:0,bottom:0,child:IconButton.filled(')
end=s.index('\n ])),',start)
old=s[start:end]
assert 'Icons.photo_camera_outlined' in old and 'Icons.delete_outline' in old
s=s[:start]+"""  Positioned(right:0,bottom:0,child:IconButton.filled(
   tooltip:'Редактировать фотографию',onPressed:_avatarActions,
   icon:const Icon(Icons.edit_outlined)))"""+s[end:]
anchor=' Future<void> _changePhoto()async{'
assert s.count(anchor)==1
actions=""" Future<void> _avatarActions()async{
  final id=SessionService.instance.currentUser.id;
  final hasPhoto=AvatarStore.instance.bytes(id)!=null;
  final choice=await showModalBottomSheet<String>(
    context:context,builder:(sheet)=>SafeArea(child:Wrap(children:[
      const Padding(padding:EdgeInsets.fromLTRB(16,18,16,8),
        child:Text('Фотография профиля',style:TextStyle(
          fontSize:18,fontWeight:FontWeight.w700))),
      ListTile(leading:const Icon(Icons.photo_library_outlined),
        title:Text(hasPhoto?'Редактировать фото':'Добавить фото'),
        subtitle:const Text('Выбрать фотографию и настроить аватарку'),
        onTap:()=>Navigator.pop(sheet,'edit')),
      ListTile(leading:const Icon(Icons.delete_outline),
        title:const Text('Удалить фото'),enabled:hasPhoto,
        onTap:hasPhoto?()=>Navigator.pop(sheet,'delete'):null),
      const SizedBox(height:12),
    ])),
  );
  if(!mounted)return;
  if(choice=='edit')await _changePhoto();
  if(choice=='delete')await _deletePhoto();
 }
 Future<void> _deletePhoto()async{
  final confirmed=await showDialog<bool>(context:context,
    builder:(dialog)=>AlertDialog(
      title:const Text('Удалить фотографию?'),
      content:const Text('Фотография исчезнет из профиля и раздела «Персонал».'),
      actions:[
        TextButton(onPressed:()=>Navigator.pop(dialog,false),
          child:const Text('Отмена')),
        FilledButton(onPressed:()=>Navigator.pop(dialog,true),
          child:const Text('Удалить')),
      ],
    ));
  if(confirmed!=true)return;
  try{
    await AvatarStore.instance.remove(SessionService.instance.currentUser.id);
    SyncService.instance.markStateDirty();
    if(mounted)ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content:Text('Фотография удалена')));
  }catch(e){
    if(mounted)ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content:Text('Не удалось удалить фотографию: $e')));
  }
 }
"""
s=s.replace(anchor,actions+anchor,1)
p.write_text(s,encoding='utf-8')
assert s.count('Positioned(right:0,bottom:0')==1
assert '_avatarActions' in s and '_deletePhoto' in s
print('PASS one pencil icon with photo editing and deletion')
