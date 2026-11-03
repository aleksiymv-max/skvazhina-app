from pathlib import Path
p=Path('lib/features/organization/profile_screen.dart')
s=p.read_text()
old="ListTile(title:const Text('ФИО'),subtitle:Text(u.name)),"
assert s.count(old)==1
new="""ListenableBuilder(listenable:SessionService.instance,builder:(ctx,_){
       final me=SessionService.instance.currentUser;
       return ListTile(
         title:const Text('ФИО'),
         subtitle:Text(me.name),
         trailing:const Icon(Icons.edit_outlined),
         onTap:_editFullName,
       );
     }),"""
s=s.replace(old,new,1)
anchor=" Future<void> _changePhoto()async{"
assert s.count(anchor)==1
method=""" Future<void> _editFullName()async{
   final editor=TextEditingController(text:SessionService.instance.currentUser.name);
   var saving=false;
   try{
     await showDialog<void>(context:context,
       builder:(ctx)=>StatefulBuilder(builder:(ctx,update)=>AlertDialog(
         title:const Text('Изменить ФИО'),
         content:TextField(controller:editor,
           autofocus:true,maxLength:160,
           textCapitalization:TextCapitalization.words,
           decoration:const InputDecoration(
             labelText:'Фамилия Имя Отчество',
             helperText:'Не менее двух слов'),
         ),
         actions:[
           TextButton(onPressed:saving?null:()=>Navigator.pop(ctx),
             child:const Text('Отмена')),
           FilledButton(onPressed:saving?null:()async{
             update(()=>saving=true);
             try{
               await SessionService.instance.changeOwnFullName(editor.text);
               if(ctx.mounted)Navigator.pop(ctx);
               if(mounted)ScaffoldMessenger.of(context).showSnackBar(
                 const SnackBar(content:Text('ФИО изменено')));
             }catch(e){
               if(ctx.mounted)update(()=>saving=false);
               if(mounted)ScaffoldMessenger.of(context).showSnackBar(
                 SnackBar(content:Text('Не удалось изменить ФИО: $e')));
             }
           },child:Text(saving?'Сохранение…':'Сохранить')),
         ],
       )),
     );
   }finally{editor.dispose();}
 }
"""
s=s.replace(anchor,method+anchor,1)
p.write_text(s)
assert '_editFullName' in s
print('PASS own name edit in personal details')
