import 'dart:typed_data';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:oilman_app/core/services/avatar_store.dart';
import 'package:oilman_app/core/services/promysel_decimal_input.dart';

void main(){
  TestWidgetsFlutterBinding.ensureInitialized();

  test('decimal input supports comma or dot, integer PKV remains integer',(){
    const blank=TextEditingValue(text:'');
    TextEditingValue next(String s)=>PromyselDecimalInput.decimal
      .formatEditUpdate(blank,TextEditingValue(text:s));
    expect(next('12,5').text,'12,5');
    expect(next('12.5').text,'12.5');
    expect(PromyselDecimalInput.parse('12,5'),12.5);
    expect(PromyselDecimalInput.parse('12.5'),12.5);
    expect(next('12,,5').text,'');
    expect(next('12.5,5').text,'');
    expect(PromyselDecimalInput.integer
      .formatEditUpdate(blank,const TextEditingValue(text:'8,5')).text,'');
    expect(PromyselDecimalInput.integer
      .formatEditUpdate(blank,const TextEditingValue(text:'8')).text,'8');
  });

  test('comma insertion respects caret and avoids duplicate separator',(){
    final c=TextEditingController(text:'123');
    c.selection=const TextSelection.collapsed(offset:2);
    PromyselDecimalInput.insertComma(c);
    expect(c.text,'12,3');
    expect(c.selection.baseOffset,3);
    PromyselDecimalInput.insertComma(c);
    expect(c.text,'12,3');
    c.dispose();
  });

  test('deleted avatar survives old snapshots and app restart queue',()async{
    SharedPreferences.setMockInitialValues({});
    final avatars=AvatarStore.instance;
    const user='11111111-1111-4111-8111-111111111111',field='field-test';
    await avatars.ensureLoaded();
    await avatars.setBytes(user,Uint8List.fromList([1,2,3]),fieldId:field);
    final set=avatars.pendingFor(user,field)!;
    expect(avatars.bytes(user),isNotNull);
    await avatars.accepted(user,field,set['operationId'] as String,1);
    expect(avatars.pendingFor(user,field),isNull);
    await avatars.remove(user,fieldId:field);
    final deletion=avatars.pendingFor(user,field)!;
    expect(deletion['expectedRevision'],1);
    expect(avatars.bytes(user),isNull);
    await avatars.apply({user:'AQID'},fieldId:field,revisions:{user:1});
    expect(avatars.bytes(user),isNull); // pending tombstone wins
    await avatars.accepted(user,field,deletion['operationId'] as String,2);
    await avatars.apply({user:'AQID'},fieldId:field,revisions:{user:1});
    expect(avatars.bytes(user),isNull); // older response cannot restore
    await avatars.apply({user:'__deleted__'},fieldId:field,revisions:{user:2});
    expect(avatars.bytes(user),isNull);
    expect(avatars.pendingFor(user,field),isNull);
    await avatars.setBytes(user,[5,6,7],fieldId:field);
    expect(avatars.pendingFor(user,field)!['expectedRevision'],2);
  });
}
