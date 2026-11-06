import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'promysel_about_screen_v215.dart';

/// Secondary sections remain on their original routes and deep links.
class PromyselMenuScreen extends StatelessWidget {
 const PromyselMenuScreen({super.key});
 @override Widget build(BuildContext context)=>Scaffold(
  appBar:AppBar(title:const Text('Меню')),
  body:ListView(padding:const EdgeInsets.all(16),children:[
   _entry(context,Icons.person_outline,'Профиль',
    'Личные данные, график работы, обучение, настройки','/profile'),
   _entry(context,Icons.oil_barrel_outlined,'Скважины',
    'Месторождение, кустовые площадки и скважины','/wells'),
   _entry(context,Icons.history_outlined,'История',
    'История обходов, параметры и журналы','/history'),
   Card(
     margin:const EdgeInsets.only(bottom:10),
     child:ListTile(
       contentPadding:const EdgeInsets.symmetric(horizontal:16,vertical:5),
       leading:const Icon(Icons.info_outline,size:26),
       title:const Text('О приложении',
         style:TextStyle(fontWeight:FontWeight.w700)),
       subtitle:const Text('О системе, руководство, версии, связь с сервером'),
       trailing:const Icon(Icons.chevron_right),
       onTap:()=>Navigator.of(context).push(MaterialPageRoute<void>(
         builder:(_)=>const PromyselAboutScreen())),
     ),
   ),
  ]),
 );
 Widget _entry(BuildContext context,IconData icon,String title,
  String subtitle,String path)=>Card(
   margin:const EdgeInsets.only(bottom:10),
   child:ListTile(
    contentPadding:const EdgeInsets.symmetric(horizontal:16,vertical:5),
    leading:Icon(icon,size:26),
    title:Text(title,style:const TextStyle(fontWeight:FontWeight.w700)),
    subtitle:Text(subtitle),
    trailing:const Icon(Icons.chevron_right),
    onTap:()=>context.go(path),
   ),
  );
}
