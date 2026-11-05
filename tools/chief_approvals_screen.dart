import 'package:flutter/material.dart';
import 'package:share_plus/share_plus.dart';
import '../../core/services/session_service.dart';
import '../../core/models/user.dart';

/// Only shows pending registration requests for the chief's current field.
/// The share link conveys field context, not authorization.
class ChiefApprovalsScreen extends StatefulWidget {
  const ChiefApprovalsScreen({super.key});
  @override
  State<ChiefApprovalsScreen> createState() => _ChiefApprovalsScreenState();
}

class _ChiefApprovalsScreenState extends State<ChiefApprovalsScreen> {
  final s=SessionService.instance;
  bool loading=false;
  String? error;
  String? deciding;

  @override
  void initState(){
    super.initState();
    s.addListener(_updated);
    WidgetsBinding.instance.addPostFrameCallback((_){if(mounted)_refresh();});
  }

  @override
  void dispose(){s.removeListener(_updated);super.dispose();}
  void _updated(){if(mounted)setState((){});}

  Future<void> _refresh()async{
    if(loading)return;
    setState((){loading=true;error=null;});
    try{await s.refreshPending(force:true).timeout(const Duration(seconds:20));}
    catch(e){if(mounted)setState(()=>error=e.toString().replaceFirst('Exception: ',''));}
    finally{if(mounted)setState(()=>loading=false);}
  }

  Future<void> _shareInvite()async{
    final fieldId=s.currentFieldId;
    if(fieldId==null||fieldId.isEmpty)return;
    // Share the registration page on the host actually serving the app.
    // TUQO installations must not redirect invited workers to Cloudflare.
    final current=Uri.base;
    final host=current.host.toLowerCase();
    final fromPublishedWeb=current.scheme=='https'&&
       (host.endsWith('.tuqo.app')||
        host.endsWith('.tuqo.ru')||
        host.endsWith('.pages.dev'));
    final domain=fromPublishedWeb?current.authority:'promysel-app.tuqo.app';
    final url=Uri.https(domain,'/login',{
      'register':'1','fieldId':fieldId,
    });
    try{
      await Share.share('Приглашение в приложение «Промысел» для месторождения «${s.fieldName(fieldId)}». Зарегистрируйтесь по ссылке: $url');
    }catch(e){
      if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(
        content:Text('Не удалось открыть меню отправки: $e')));
    }
  }

  Future<void> _decide(String requestId,String name,bool approve)async{
    if(deciding!=null)return;
    final confirm=await showDialog<bool>(context:context,builder:(ctx)=>AlertDialog(
      title:Text(approve?'Согласовать сотрудника?':'Отклонить заявку?'),
      content:Text(name),
      actions:[
        TextButton(onPressed:()=>Navigator.pop(ctx,false),child:const Text('Отмена')),
        FilledButton(onPressed:()=>Navigator.pop(ctx,true),
          child:Text(approve?'Согласовать':'Отклонить')),
      ],
    ));
    if(confirm!=true||!mounted)return;
    setState(()=>deciding=requestId);
    try{
      await s.ensureFreshToken();
      if(approve){await s.approveRemote(requestId);}
      else{await s.rejectRemote(requestId);}
      if(!mounted)return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
        content:Text(approve?'Заявка согласована':'Заявка отклонена')));
      await _refresh();
    }catch(e){
      if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(
        content:Text('Не удалось обработать заявку: ${e.toString().replaceFirst('Exception: ','')}')));
    }finally{if(mounted)setState(()=>deciding=null);}
  }

  @override
  Widget build(BuildContext context){
    if(s.currentUser.role!=UserRole.shopChief){
      return Scaffold(appBar:AppBar(title:const Text('Согласование')),
        body:const Center(child:Text('Раздел доступен только начальнику цеха')));
    }
    final field=s.currentFieldId;
    final pending=s.allPending.where((p)=>p.fieldId==field).toList();
    return Scaffold(
      appBar:AppBar(title:const Text('Согласование'),actions:[
        IconButton(tooltip:'Обновить заявки',onPressed:loading?null:_refresh,
          icon:const Icon(Icons.refresh)),
      ]),
      body:RefreshIndicator(onRefresh:_refresh,child:ListView(
        padding:const EdgeInsets.all(16),
        children:[
          FilledButton.icon(onPressed:_shareInvite,icon:const Icon(Icons.share_outlined),
            label:const Text('Пригласить сотрудника')),
          const SizedBox(height:12),
          Text('Месторождение: ${s.fieldName(field??'')}',
            style:Theme.of(context).textTheme.titleMedium),
          const SizedBox(height:12),
          if(loading)const LinearProgressIndicator(minHeight:2),
          if(error!=null)Card(child:ListTile(
            leading:const Icon(Icons.error_outline),
            title:const Text('Не удалось загрузить заявки'),
            subtitle:Text(error!),
            trailing:TextButton(onPressed:_refresh,child:const Text('Повторить')))),
          if(!loading&&error==null&&pending.isEmpty)
            const Card(child:ListTile(
              title:Text('Нет заявок, ожидающих решения'),
              subtitle:Text('Потяните вниз, чтобы проверить новые заявки'))),
          ...pending.map((p)=>Card(child:Padding(
            padding:const EdgeInsets.all(12),
            child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[
              Text(p.name,style:Theme.of(context).textTheme.titleMedium),
              const SizedBox(height:5),
              Text(p.role.label,style:Theme.of(context).textTheme.bodyMedium),
              const SizedBox(height:10),
              Wrap(spacing:8,runSpacing:8,children:[
                OutlinedButton(onPressed:deciding==null?
                  ()=>_decide(p.id,p.name,false):null,child:const Text('Отклонить')),
                FilledButton(onPressed:deciding==null?
                  ()=>_decide(p.id,p.name,true):null,
                  child:deciding==p.id?const SizedBox(height:18,width:18,
                    child:CircularProgressIndicator(strokeWidth:2)):
                    const Text('Согласовать')),
              ]),
            ]),
          ))),
        ],
      )),
    );
  }
}
