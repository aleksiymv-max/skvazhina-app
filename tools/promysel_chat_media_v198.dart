import 'dart:async';
import 'dart:collection';
import 'dart:math' as math;

import 'package:audioplayers/audioplayers.dart';
import 'package:flutter/material.dart';
import 'package:video_player/video_player.dart';
import '../../core/services/promysel_chat_service.dart';

/// A single player for the open conversation. Never create one network video
/// decoder for every message in the scrollable history.
class ChatMediaHub extends ChangeNotifier {
  final LinkedHashMap<String,String> _visibleVideos=LinkedHashMap<String,String>();
  final Set<String> _suppressed=<String>{};
  VideoPlayerController? video;
  AudioPlayer? audio;
  StreamSubscription<Duration>? _audioPosition,_audioDuration;
  StreamSubscription<PlayerState>? _audioState;
  int _generation=0;
  bool _disposed=false;
  DateTime _lastUpdate=DateTime.fromMillisecondsSinceEpoch(0);
  String? messageId;
  String kind='';
  bool mini=false,expanded=false,loading=false,playing=false,muted=true;
  String? error;
  double speed=1;
  Duration position=Duration.zero,duration=Duration.zero;

  void _emit({bool immediate=true}){
    if(_disposed)return;
    final now=DateTime.now();
    if(!immediate&&now.difference(_lastUpdate)<const Duration(milliseconds:230))return;
    _lastUpdate=now;
    notifyListeners();
  }
  double get progress=>duration.inMilliseconds<=0?0:
    (position.inMilliseconds/duration.inMilliseconds).clamp(0.0,1.0);
  void _videoTick(){
    final v=video?.value;
    if(v==null||!v.isInitialized)return;
    position=v.position;duration=v.duration;
    final changed=playing!=v.isPlaying;
    playing=v.isPlaying;
    if(v.hasError){error=v.errorDescription??'Ошибка загрузки видео';loading=false;}
    _emit(immediate:changed||v.hasError);
  }
  Future<void> _release()async{
    final v=video;video=null;
    if(v!=null){v.removeListener(_videoTick);unawaited(v.dispose());}
    await _audioPosition?.cancel();_audioPosition=null;
    await _audioDuration?.cancel();_audioDuration=null;
    await _audioState?.cancel();_audioState=null;
    final a=audio;audio=null;
    if(a!=null)unawaited(a.dispose());
  }
  Future<void> _loadVideo(String id,String url,{required bool preview})async{
    if(_disposed||url.isEmpty)return;
    final gen=++_generation;
    await _release();
    if(_disposed||gen!=_generation)return;
    messageId=id;kind='video';mini=!preview;expanded=!preview;
    loading=true;playing=false;muted=preview;error=null;
    position=Duration.zero;duration=Duration.zero;speed=1;
    _emit();
    final c=VideoPlayerController.networkUrl(
      Uri.parse(url),videoPlayerOptions:VideoPlayerOptions(mixWithOthers:true));
    video=c;
    c.addListener(_videoTick);
    try{
      await c.initialize().timeout(const Duration(seconds:22));
      if(_disposed||gen!=_generation)return;
      await c.setLooping(preview);
      await c.setVolume(preview?0:1);
      await c.setPlaybackSpeed(speed);
      await c.play();
      if(_disposed||gen!=_generation)return;
      loading=false;duration=c.value.duration;playing=true;_emit();
    }catch(e){
      if(!_disposed&&gen==_generation){
        loading=false;error='Видео недоступно. Нажмите, чтобы повторить.';
        playing=false;_emit();
      }
    }
  }
  void videoVisible(String id,String url,bool visible){
    if(_disposed)return;
    if(visible){
      if(!_visibleVideos.containsKey(id))_visibleVideos[id]=url;
    }else{
      _visibleVideos.remove(id);_suppressed.remove(id);
    }
    if(mini||expanded)return;
    // Only one decoder is active; the most recently visible round video wins.
    final target=_visibleVideos.isEmpty?null:_visibleVideos.keys.last;
    if(target==null){
      if(kind=='video'&&messageId!=null)unawaited(_stopInternal());
    }else if((messageId!=target||error!=null)&&!_suppressed.contains(target)){
      unawaited(_loadVideo(target,_visibleVideos[target]!,preview:true));
    }
  }
  Future<void> openVideo(String id,String url)async{
    if(_disposed)return;
    if(kind=='video'&&messageId==id&&video?.value.isInitialized==true){
      mini=true;expanded=true;muted=false;error=null;
      await video!.setLooping(false);
      await video!.setVolume(1);
      await video!.play();
      playing=true;_emit();return;
    }
    await _loadVideo(id,url,preview:false);
  }
  Future<void> closeExpanded()async{
    if(_disposed||kind!='video')return;
    expanded=false;muted=true;
    try{await video?.setVolume(0);await video?.setLooping(true);}catch(_){}
    _emit();
  }
  Future<void> playVoice(String id,String url)async{
    if(_disposed||url.isEmpty)return;
    if(kind=='voice'&&messageId==id){await toggle();return;}
    final gen=++_generation;
    await _release();
    if(_disposed||gen!=_generation)return;
    messageId=id;kind='voice';mini=true;expanded=false;
    muted=false;loading=true;playing=false;error=null;speed=1;
    position=Duration.zero;duration=Duration.zero;_emit();
    final a=AudioPlayer();audio=a;
    _audioPosition=a.onPositionChanged.listen((p){position=p;_emit(immediate:false);});
    _audioDuration=a.onDurationChanged.listen((d){duration=d;_emit();});
    _audioState=a.onPlayerStateChanged.listen((s){
      playing=s==PlayerState.playing;loading=false;_emit();
    });
    try{
      await a.play(UrlSource(url));
      if(gen==_generation&&!_disposed){loading=false;playing=true;_emit();}
    }catch(e){
      if(gen==_generation&&!_disposed){
        loading=false;playing=false;error='Аудио недоступно. Повторите попытку.';_emit();
      }
    }
  }
  Future<void> toggle()async{
    try{
      if(kind=='video'&&video?.value.isInitialized==true){
        if(video!.value.isPlaying){await video!.pause();}else{
          if(duration>Duration.zero&&position>=duration)await video!.seekTo(Duration.zero);
          await video!.play();
        }
        playing=video!.value.isPlaying;
      }else if(kind=='voice'&&audio!=null){
        if(playing)await audio!.pause();else{
          if(duration>Duration.zero&&position>=duration)await audio!.seek(Duration.zero);
          await audio!.resume();
        }
        playing=!playing;
      }
      _emit();
    }catch(e){error='Не удалось изменить воспроизведение';_emit();}
  }
  Future<void> setSpeed(double value)async{
    if(_disposed)return;
    try{
      if(kind=='video')await video?.setPlaybackSpeed(value);
      if(kind=='voice')await audio?.setPlaybackRate(value);
      speed=value;_emit();
    }catch(e){error='Не удалось изменить скорость';_emit();}
  }
  Future<void> seek(double fraction)async{
    if(_disposed||duration.inMilliseconds<=0)return;
    final target=Duration(milliseconds:(duration.inMilliseconds*fraction.clamp(0.0,1.0)).round());
    try{
      if(kind=='video')await video?.seekTo(target);
      if(kind=='voice')await audio?.seek(target);
      position=target;_emit();
    }catch(_){}
  }
  Future<void> setMuted(bool value)async{
    if(kind!='video')return;
    try{await video?.setVolume(value?0:1);muted=value;_emit();}catch(_){}
  }
  Future<void> _stopInternal()async{
    ++_generation;
    messageId=null;kind='';mini=false;expanded=false;loading=false;
    playing=false;error=null;position=Duration.zero;duration=Duration.zero;
    _emit();
    await _release();
  }
  Future<void> stop()async{
    if(messageId!=null)_suppressed.add(messageId!);
    await _stopInternal();
  }
  @override void dispose(){
    _disposed=true;++_generation;
    _visibleVideos.clear();
    unawaited(_release());
    super.dispose();
  }
}

String _chatMediaTime(Duration d){
  final secs=d.inSeconds.clamp(0,999999);
  return (secs~/60).toString()+':'+(secs%60).toString().padLeft(2,'0');
}

class ChatMediaBar extends StatelessWidget{
  const ChatMediaBar({super.key,required this.hub});
  final ChatMediaHub hub;
  @override Widget build(BuildContext context)=>AnimatedBuilder(animation:hub,builder:(context,child){
    if(!hub.mini||hub.messageId==null)return const SizedBox.shrink();
    final colors=Theme.of(context).colorScheme;
    return Container(
      padding:const EdgeInsets.fromLTRB(8,3,4,5),
      decoration:BoxDecoration(color:colors.surfaceContainerHigh,
        border:Border(bottom:BorderSide(color:colors.outlineVariant.withValues(alpha:.4)))),
      child:Column(mainAxisSize:MainAxisSize.min,children:[
        Row(children:[
          IconButton.filledTonal(
            tooltip:hub.playing?'Пауза':'Воспроизвести',
            onPressed:hub.loading?null:()=>hub.toggle(),
            icon:hub.loading?
              const SizedBox.square(dimension:17,child:CircularProgressIndicator(strokeWidth:2)):
              Icon(hub.playing?Icons.pause_rounded:Icons.play_arrow_rounded)),
          const SizedBox(width:7),
          Icon(hub.kind=='voice'?Icons.graphic_eq_rounded:Icons.video_camera_front_rounded,
            size:22,color:colors.primary),
          const SizedBox(width:8),
          Expanded(child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[
            Text(hub.kind=='voice'?'Голосовое сообщение':'Видеосообщение',
              maxLines:1,overflow:TextOverflow.ellipsis,
              style:const TextStyle(fontWeight:FontWeight.w700,fontSize:12.5)),
            Text(hub.error??(_chatMediaTime(hub.position)+' / '+_chatMediaTime(hub.duration)),
              maxLines:1,overflow:TextOverflow.ellipsis,
              style:TextStyle(fontSize:11,color:colors.onSurfaceVariant)),
          ])),
          if(hub.kind=='video')IconButton(
            tooltip:hub.muted?'Включить звук':'Выключить звук',
            onPressed:()=>hub.setMuted(!hub.muted),
            icon:Icon(hub.muted?Icons.volume_off_rounded:Icons.volume_up_rounded,size:19)),
          PopupMenuButton<double>(
            tooltip:'Скорость воспроизведения',
            initialValue:hub.speed,
            onSelected:(v)=>hub.setSpeed(v),
            itemBuilder:(_)=>[0.5,1.0,1.5,2.0].map((v)=>PopupMenuItem<double>(
              value:v,child:Text(v.toStringAsFixed(v==1?0:1)+'×'))).toList(),
            child:Padding(padding:const EdgeInsets.symmetric(horizontal:6,vertical:10),
              child:Text(hub.speed.toStringAsFixed(hub.speed==1?0:1)+'×',
                style:TextStyle(fontWeight:FontWeight.bold,fontSize:12,color:colors.primary)))),
          IconButton(tooltip:'Закрыть проигрыватель',
            onPressed:()=>hub.stop(),icon:const Icon(Icons.close_rounded,size:21)),
        ]),
        GestureDetector(
          behavior:HitTestBehavior.opaque,
          onTapDown:(d){
            final box=context.findRenderObject() as RenderBox?;
            if(box!=null&&box.size.width>0)hub.seek(d.localPosition.dx/box.size.width);
          },
          child:Padding(padding:const EdgeInsets.symmetric(horizontal:9,vertical:3),
            child:LinearProgressIndicator(value:hub.progress,minHeight:3,borderRadius:BorderRadius.circular(4)))),
      ]),
    );
  });
}

class ChatVoiceMedia extends StatefulWidget{
  const ChatVoiceMedia({super.key,required this.hub,required this.roomId,required this.message,
    required this.onError});
  final ChatMediaHub hub;
  final String roomId;
  final Map<String,dynamic> message;
  final void Function(Object) onError;
  @override State<ChatVoiceMedia> createState()=>_ChatVoiceMediaState();
}
class _ChatVoiceMediaState extends State<ChatVoiceMedia>{
  String? transcript;
  bool transcribing=false;
  @override void initState(){super.initState();transcript=widget.message['transcript']?.toString();}
  Future<void> _transcribe()async{
    if(transcribing)return;
    if(transcript!=null&&transcript!.isNotEmpty){setState(()=>transcript=null);return;}
    final ok=await showDialog<bool>(context:context,builder:(c)=>AlertDialog(
      title:const Text('Распознать голосовое сообщение?'),
      content:const Text('Запись будет обработана серверным сервисом.'),
      actions:[
        TextButton(onPressed:()=>Navigator.pop(c,false),child:const Text('Отмена')),
        FilledButton(onPressed:()=>Navigator.pop(c,true),child:const Text('Распознать')),
      ]));
    if(ok!=true||!mounted)return;
    setState(()=>transcribing=true);
    try{
      final value=await PromyselChatService.instance.transcribe(widget.roomId,
        widget.message['id'].toString());
      if(mounted)setState(()=>transcript=value);
    }catch(e){widget.onError(e);}
    finally{if(mounted)setState(()=>transcribing=false);}
  }
  @override Widget build(BuildContext context)=>AnimatedBuilder(animation:widget.hub,builder:(context,_){
    final id=widget.message['id'].toString();
    final selected=widget.hub.messageId==id&&widget.hub.kind=='voice';
    final position=selected?widget.hub.position:Duration.zero;
    final stored=(widget.message['duration_ms'] as num?)?.toInt()??0;
    final duration=selected&&widget.hub.duration>Duration.zero?widget.hub.duration:
      Duration(milliseconds:stored);
    final levels=(widget.message['waveform'] as List?)?.whereType<num>()
      .map((e)=>e.toDouble().clamp(0.0,1.0).toDouble()).toList()??const <double>[];
    return ConstrainedBox(constraints:const BoxConstraints(maxWidth:288),child:
      Column(crossAxisAlignment:CrossAxisAlignment.start,children:[
        Row(children:[
          IconButton.filledTonal(
            tooltip:selected&&widget.hub.playing?'Пауза':'Воспроизвести',
            onPressed:()=>widget.hub.playVoice(id,widget.message['url']?.toString()??''),
            icon:Icon(selected&&widget.hub.playing?Icons.pause_rounded:Icons.play_arrow_rounded)),
          const SizedBox(width:6),
          Expanded(child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[
            SizedBox(height:32,child:CustomPaint(
              painter:_VoiceBars(levels,
                selected?widget.hub.progress:0,
                Theme.of(context).colorScheme.primary),
              child:SizedBox.expand(child:GestureDetector(onTapDown:(details){
                if(selected)widget.hub.seek(details.localPosition.dx/170);
                else widget.hub.playVoice(id,widget.message['url']?.toString()??'');
              })))),
            Text(_chatMediaTime(position)+' / '+_chatMediaTime(duration),
              style:Theme.of(context).textTheme.labelSmall),
          ])),
          TextButton(onPressed:transcribing?null:_transcribe,
            child:transcribing?
              const SizedBox.square(dimension:16,child:CircularProgressIndicator(strokeWidth:2)):
              const Text('Aa',style:TextStyle(fontWeight:FontWeight.bold))),
        ]),
        if(transcript!=null&&transcript!.isNotEmpty)
          Padding(padding:const EdgeInsets.only(top:5),
            child:Text(transcript!,style:const TextStyle(fontSize:13.5,height:1.4))),
      ]));
  });
}
class _VoiceBars extends CustomPainter{
  const _VoiceBars(this.levels,this.progress,this.color);
  final List<double> levels;final double progress;final Color color;
  @override void paint(Canvas canvas,Size size){
    const count=38;
    final width=size.width/count;
    for(var i=0;i<count;i++){
      final amplitude=levels.isNotEmpty?
        levels[(i*levels.length/count).floor().clamp(0,levels.length-1)]:
        (0.28+0.55*math.sin(i*1.7).abs());
      final barHeight=5+amplitude*(size.height-8);
      final paint=Paint()..color=i/count<=progress?color:color.withValues(alpha:.35);
      canvas.drawRRect(RRect.fromRectAndRadius(
        Rect.fromLTWH(width*i,(size.height-barHeight)/2,math.max(2.0,width-2),barHeight),
        const Radius.circular(3)),paint);
    }
  }
  @override bool shouldRepaint(_VoiceBars prev)=>
    prev.progress!=progress||prev.color!=color||prev.levels!=levels;
}

class ChatVideoMedia extends StatefulWidget{
  const ChatVideoMedia({super.key,required this.hub,required this.id,
    required this.url,required this.scroll});
  final ChatMediaHub hub;final String id,url;final ScrollController scroll;
  @override State<ChatVideoMedia> createState()=>_ChatVideoMediaState();
}
class _ChatVideoMediaState extends State<ChatVideoMedia>{
  final GlobalKey _marker=GlobalKey();
  bool _visible=false;
  @override void initState(){
    super.initState();
    widget.scroll.addListener(_check);
    WidgetsBinding.instance.addPostFrameCallback((_){_check();});
  }
  @override void didUpdateWidget(covariant ChatVideoMedia old){
    super.didUpdateWidget(old);
    if(old.scroll!=widget.scroll){old.scroll.removeListener(_check);widget.scroll.addListener(_check);}
    // Signed playback links can rotate on every history refresh. Keep the
    // already initialized decoder when the immutable message ID is unchanged.
    if(old.id!=widget.id){
      widget.hub.videoVisible(old.id,old.url,false);_visible=false;
      WidgetsBinding.instance.addPostFrameCallback((_){_check();});
    }
  }
  void _check(){
    if(!mounted)return;
    final obj=_marker.currentContext?.findRenderObject();
    if(obj is! RenderBox||!obj.attached||!obj.hasSize)return;
    final start=obj.localToGlobal(Offset.zero).dy;
    final height=obj.size.height;
    final screen=MediaQuery.sizeOf(context).height;
    final visible=start<screen-125&&start+height>110;
    if(visible!=_visible){
      _visible=visible;
      widget.hub.videoVisible(widget.id,widget.url,visible);
    }
  }
  @override void dispose(){
    widget.scroll.removeListener(_check);
    if(_visible)widget.hub.videoVisible(widget.id,widget.url,false);
    super.dispose();
  }
  Future<void> _open()async{
    final task=widget.hub.openVideo(widget.id,widget.url);
    if(!mounted)return;
    await showDialog<void>(context:context,builder:(c)=>ChatVideoViewer(hub:widget.hub));
    await widget.hub.closeExpanded();
    await task;
  }
  @override Widget build(BuildContext context)=>SizedBox(
    key:_marker,width:210,height:210,
    child:GestureDetector(onTap:_open,child:ChatRoundVideoSurface(hub:widget.hub,id:widget.id,size:210)));
}

class ChatRoundVideoSurface extends StatelessWidget{
  const ChatRoundVideoSurface({super.key,required this.hub,required this.id,required this.size});
  final ChatMediaHub hub;final String id;final double size;
  @override Widget build(BuildContext context)=>AnimatedBuilder(animation:hub,builder:(context,_){
    final active=hub.kind=='video'&&hub.messageId==id;
    final c=active?hub.video:null;
    final ready=c?.value.isInitialized==true;
    return ClipOval(child:SizedBox.square(dimension:size,child:Stack(fit:StackFit.expand,children:[
      ColoredBox(color:Theme.of(context).colorScheme.surfaceContainerHighest),
      if(ready)
        FittedBox(fit:BoxFit.cover,child:SizedBox(
          width:c!.value.size.width>0?c.value.size.width:210,
          height:c.value.size.height>0?c.value.size.height:210,
          child:VideoPlayer(c)))
      else
        Center(child:active&&hub.loading?
          const SizedBox.square(dimension:32,child:CircularProgressIndicator(strokeWidth:3)):
          Icon(hub.error!=null?Icons.refresh_rounded:Icons.play_circle_fill_rounded,
            color:Theme.of(context).colorScheme.primary,size:56)),
      if(ready&&!hub.playing)
        const Center(child:Icon(Icons.play_circle_fill_rounded,color:Colors.white,size:54)),
      if(ready)
        Positioned.fill(child:IgnorePointer(child:CircularProgressIndicator(
          value:hub.progress,strokeWidth:3.3,color:Colors.white,
          backgroundColor:Colors.white24))),
      if(ready)
        Positioned(left:17,bottom:14,child:DecoratedBox(
          decoration:BoxDecoration(color:Colors.black54,borderRadius:BorderRadius.circular(9)),
          child:Padding(padding:const EdgeInsets.symmetric(horizontal:7,vertical:3),
            child:Text(_chatMediaTime(hub.position),
              style:const TextStyle(color:Colors.white,fontSize:11.5,fontWeight:FontWeight.bold))))),
    ])));
  });
}
class ChatVideoViewer extends StatelessWidget{
  const ChatVideoViewer({super.key,required this.hub});
  final ChatMediaHub hub;
  @override Widget build(BuildContext context)=>Dialog(
    backgroundColor:Theme.of(context).colorScheme.surface,
    insetPadding:const EdgeInsets.symmetric(horizontal:18,vertical:24),
    shape:RoundedRectangleBorder(borderRadius:BorderRadius.circular(22)),
    child:Padding(padding:const EdgeInsets.fromLTRB(12,16,12,10),child:
      Column(mainAxisSize:MainAxisSize.min,children:[
        const Text('Видеосообщение',style:TextStyle(fontSize:16,fontWeight:FontWeight.w700)),
        const SizedBox(height:15),
        AnimatedBuilder(animation:hub,builder:(c,_)=>ChatRoundVideoSurface(
          hub:hub,id:hub.messageId??'',size:
            math.min(MediaQuery.sizeOf(context).width-64,345.0))),
        const SizedBox(height:10),
        AnimatedBuilder(animation:hub,builder:(c,_)=>Row(
          mainAxisAlignment:MainAxisAlignment.center,children:[
            IconButton.filledTonal(
              tooltip:hub.playing?'Пауза':'Воспроизвести',
              onPressed:hub.loading?null:()=>hub.toggle(),
              icon:Icon(hub.playing?Icons.pause_rounded:Icons.play_arrow_rounded)),
            IconButton(
              tooltip:hub.muted?'Включить звук':'Выключить звук',
              onPressed:()=>hub.setMuted(!hub.muted),
              icon:Icon(hub.muted?Icons.volume_off_rounded:Icons.volume_up_rounded)),
            PopupMenuButton<double>(
              tooltip:'Скорость',
              initialValue:hub.speed,onSelected:(v)=>hub.setSpeed(v),
              itemBuilder:(_)=>[0.5,1.0,1.5,2.0].map((v)=>
                PopupMenuItem<double>(value:v,child:Text(v.toString()+'×'))).toList(),
              child:Padding(padding:const EdgeInsets.all(12),
                child:Text(hub.speed.toString()+'×'))),
            IconButton(tooltip:'Закрыть',onPressed:()=>Navigator.of(context).pop(),
              icon:const Icon(Icons.close_rounded)),
          ])),
      ])));
}
