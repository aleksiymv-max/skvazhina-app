import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main(){
 testWidgets('Tap on visual-only suffix still focuses editable field',(tester)async{
   final focus=FocusNode();
   final controller=TextEditingController(text:'18,3');
   await tester.pumpWidget(MaterialApp(home:Scaffold(body:Center(
     child:SizedBox(width:350,child:TextFormField(
       controller:controller,focusNode:focus,
       decoration:const InputDecoration(labelText:'Ртр',
         suffix:IgnorePointer(child:Row(mainAxisSize:MainAxisSize.min,
           children:[Text('Было 18,6'),SizedBox(width:8),
             Text('Δ −0,3'),SizedBox(width:10),Text('МПа')])))))))));
   await tester.tapAt(tester.getCenter(find.text('Δ −0,3')));
   await tester.pump();
   expect(focus.hasFocus,isTrue);
   expect(controller.text,'18,3');
   await tester.enterText(find.byType(TextFormField),'18,4');
   expect(controller.text,'18,4');
   focus.dispose();controller.dispose();
 });
}
