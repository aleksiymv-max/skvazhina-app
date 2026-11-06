import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import '../../core/models/work_task.dart';
import '../../core/services/task_photo_service.dart';

class TaskPhotoPicker extends StatelessWidget {
  const TaskPhotoPicker({super.key,required this.photos});
  final TaskPhotoSelectionController photos;
  @override Widget build(BuildContext context)=>ListenableBuilder(
    listenable:photos,builder:(context,_)=>
      Column(mainAxisSize:MainAxisSize.min,crossAxisAlignment:CrossAxisAlignment.start,children:[
        const Text('Прикрепить фотографии (необязательно)',style:TextStyle(fontWeight:FontWeight.w700)),
        Wrap(spacing:6,runSpacing:6,children:[
          OutlinedButton.icon(onPressed:photos.picking?null:()=>photos.pick(ImageSource.camera),
            icon:const Icon(Icons.camera_alt_outlined),label:const Text('Камера')),
          OutlinedButton.icon(onPressed:photos.picking?null:()=>photos.pick(ImageSource.gallery),
            icon:const Icon(Icons.photo_library_outlined),label:const Text('Галерея')),
        ]),
        if(photos.picking)const LinearProgressIndicator(),
        if(photos.error!=null)Text(photos.error!,style:TextStyle(color:Theme.of(context).colorScheme.error)),
        if(photos.photos.isNotEmpty)Wrap(spacing:7,runSpacing:7,children:[
          for(final photo in photos.photos)Stack(children:[
            ClipRRect(borderRadius:BorderRadius.circular(8),
              child:Image.memory(photo.bytes,width:75,height:75,fit:BoxFit.cover)),
            Positioned(top:0,right:0,child:InkWell(onTap:()=>photos.remove(photo.id),
              child:const CircleAvatar(radius:11,backgroundColor:Colors.black87,
                child:Icon(Icons.close,color:Colors.white,size:14)))),
          ]),
        ]),
      ]));
}

class TaskPhotoGallery extends StatefulWidget {
  const TaskPhotoGallery({super.key,required this.task});
  final WorkTask task;
  @override State<TaskPhotoGallery> createState()=>_TaskPhotoGalleryState();
}
class _TaskPhotoGalleryState extends State<TaskPhotoGallery>{
  late Future<List<Map<String,dynamic>>> future;
  @override void initState(){super.initState();_reload();}
  void _reload({bool force=false}){future=TaskPhotoService.instance.list(widget.task,force:force); }
  Future<void> _open(String id)async{
    try{
      final signed=await TaskPhotoService.instance.signedUrl(id);
      if(!mounted)return;
      await Navigator.push(context,MaterialPageRoute(builder:(_)=>Scaffold(
        appBar:AppBar(title:const Text('Фотография задания')),
        body:InteractiveViewer(child:Center(child:Image.network(signed,
          errorBuilder:(_,__,___)=>const Text('Не удалось открыть фотографию')))))));
    }catch(error){
      if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(error.toString())));
    }
  }
  @override Widget build(BuildContext context)=>Scaffold(
    appBar:AppBar(title:const Text('Фото задания'),
      actions:[IconButton(onPressed:()=>setState(()=>_reload(force:true)),icon:const Icon(Icons.refresh))]),
    body:FutureBuilder<List<Map<String,dynamic>>>(future:future,builder:(context,snapshot){
      if(snapshot.connectionState!=ConnectionState.done)return const Center(child:CircularProgressIndicator());
      if(snapshot.hasError)return Center(child:Padding(padding:const EdgeInsets.all(20),
        child:Text('Ошибка загрузки: '+snapshot.error.toString())));
      final rows=snapshot.data??[];
      if(rows.isEmpty)return const Center(child:Text('К заданию фотографии не прикреплены'));
      return ListView(padding:const EdgeInsets.all(14),children:[
        Text(widget.task.title,style:Theme.of(context).textTheme.titleLarge),
        for(final row in rows)Card(child:ListTile(
          leading:const Icon(Icons.photo_outlined),
          title:Text(row['phase']=='assignment'?'При выдаче задания':'При выполнении задания'),
          subtitle:Text((row['original_name']??'Фотография').toString()+'\n'+(row['uploaded_at']??'').toString()),
          trailing:const Icon(Icons.open_in_full),onTap:()=>_open(row['id'].toString()))),
      ]);
    }));
}
