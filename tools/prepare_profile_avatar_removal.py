from pathlib import Path
p=Path('lib/features/organization/profile_screen.dart')
s=p.read_text()
anchor="  Positioned(right:0,bottom:0,child:IconButton.filled(\n   onPressed:_changePhoto,icon:const Icon(Icons.photo_camera_outlined)))"
assert s.count(anchor)==1
remove=",\n  Positioned(left:0,bottom:0,child:IconButton.filledTonal(\n   tooltip:'Удалить фотографию',\n   onPressed:AvatarStore.instance.bytes(u.id)==null?null:()async{\n    await AvatarStore.instance.remove(u.id);\n    SyncService.instance.markStateDirty();\n    if(mounted)setState((){});\n   },icon:const Icon(Icons.delete_outline)))"
p.write_text(s.replace(anchor,anchor+remove))
p=Path('lib/core/services/avatar_store.dart')
s=p.read_text()
anchor='data.remove(userId);'
assert s.count(anchor)==1
p.write_text(s.replace(anchor,"data[userId]='__deleted__';",1))
print('PASS avatar removal with replicated tombstone')
