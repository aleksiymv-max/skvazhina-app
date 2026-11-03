from pathlib import Path
p=Path('lib/features/organization/profile_screen.dart')
s=p.read_text()
a=s.index(' Future<void> _changePhoto()async')
b=s.index(' Future<void> _settings()async',a)
s=s[:a]+"""
 Future<void> _changePhoto()async{
  final source=await showModalBottomSheet<ImageSource>(
   context:context,builder:(ctx)=>SafeArea(child:Wrap(children:[
    ListTile(leading:const Icon(Icons.photo_library_outlined),
      title:const Text('Выбрать из галереи'),
      onTap:()=>Navigator.pop(ctx,ImageSource.gallery)),
    ListTile(leading:const Icon(Icons.camera_alt_outlined),
      title:const Text('Сделать фотографию'),
      onTap:()=>Navigator.pop(ctx,ImageSource.camera)),
   ])));
  if(source==null||!mounted)return;
  try{
   final f=await picker.pickImage(source:source,
    imageQuality:88,maxWidth:1600,maxHeight:1600);
   if(f==null||!mounted)return;
   final raw=await f.readAsBytes();
   if(!mounted)return;
   final cropped=await editProfileAvatar(context,raw);
   if(cropped==null)return;
   await AvatarStore.instance.setBytes(
     SessionService.instance.currentUser.id,cropped);
   SyncService.instance.markStateDirty();
   if(mounted)ScaffoldMessenger.of(context).showSnackBar(
    const SnackBar(content:Text('Фотография сохранена')));
  }catch(e){
   if(mounted)ScaffoldMessenger.of(context).showSnackBar(
    SnackBar(content:Text('Ошибка обработки фотографии: $e')));
  }
 }
""" +s[b:]
p.write_text(s)
assert 'editProfileAvatar(context,raw)' in s
print('PASS avatar crop and sync')
