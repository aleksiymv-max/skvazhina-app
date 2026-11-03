import 'dart:typed_data';
import 'dart:ui' as ui;
import 'dart:math' as math;
import 'package:flutter/material.dart';

Future<Uint8List?> editProfileAvatar(BuildContext context,Uint8List raw) async {
  final codec=await ui.instantiateImageCodec(raw);
  final frame=await codec.getNextFrame();
  codec.dispose();
  final image=frame.image;
  var zoom=1.0;
  var pan=Offset.zero;
  const side=240.0;
  try{
    return await showDialog<Uint8List>(
      context:context,
      builder:(ctx)=>StatefulBuilder(builder:(ctx,update){
        final w=image.width.toDouble(),h=image.height.toDouble();
        final base=math.max(side/w,side/h);
        final maxX=math.max(0.0,(w*base*zoom-side)/2);
        final maxY=math.max(0.0,(h*base*zoom-side)/2);
        return AlertDialog(title:const Text('Настроить аватарку'),
          content:Column(mainAxisSize:MainAxisSize.min,children:[
            const Text('Поместите лицо в круг, перемещая фотографию.'),
            const SizedBox(height:12),
            GestureDetector(onPanUpdate:(d)=>update((){
              pan=Offset((pan.dx+d.delta.dx).clamp(-maxX,maxX).toDouble(),
                (pan.dy+d.delta.dy).clamp(-maxY,maxY).toDouble());
            }),child:ClipOval(child:SizedBox(width:side,height:side,
              child:Transform.translate(offset:pan,child:Transform.scale(
                scale:zoom,child:Image.memory(raw,fit:BoxFit.cover,width:side,height:side))))),
            ),
            Slider(value:zoom,min:1,max:4,onChanged:(v)=>update((){
              zoom=v;
              pan=Offset(pan.dx.clamp(-(math.max(0.0,(w*base*zoom-side)/2)),math.max(0.0,(w*base*zoom-side)/2)).toDouble(),
                pan.dy.clamp(-(math.max(0.0,(h*base*zoom-side)/2)),math.max(0.0,(h*base*zoom-side)/2)).toDouble());
            })),
          ]),
          actions:[
            TextButton(onPressed:()=>Navigator.pop(ctx),child:const Text('Отмена')),
            FilledButton(onPressed:()async{
              final rectSide=side/(base*zoom);
              final rect=Rect.fromLTWH((w-rectSide)/2-pan.dx/(base*zoom),
                (h-rectSide)/2-pan.dy/(base*zoom),rectSide,rectSide);
              final recorder=ui.PictureRecorder();
              Canvas(recorder).drawImageRect(image,rect,
                const Rect.fromLTWH(0,0,384,384),Paint()..filterQuality=FilterQuality.high);
              final picture=recorder.endRecording();
              final cropped=await picture.toImage(384,384);
              final data=await cropped.toByteData(format:ui.ImageByteFormat.png);
              cropped.dispose();
              picture.dispose();
              if(ctx.mounted&&data!=null)Navigator.pop(ctx,data.buffer.asUint8List());
            },child:const Text('Сохранить')),
          ],
        );
      }),
    );
  }finally{image.dispose();}
}
