import 'package:flutter_test/flutter_test.dart';
import 'package:oilman_app/core/services/walk_parameter_save_rules.dart';

void main(){
  test('hidden PKV and PID do not block saving',(){
    final selected=<String>{'rtr','rz','ruzd','tuzd','choke'};
    expect(WalkParameterSaveRules.requiresProgramConfirmation(
      selected,pkvConfirmed:false,pidConfirmed:false),false);
  });
  test('only configured PKV requires a confirmation',(){
    final selected=<String>{'rtr','pkv'};
    expect(WalkParameterSaveRules.requiresProgramConfirmation(
      selected,pkvConfirmed:false,pidConfirmed:false),true);
    expect(WalkParameterSaveRules.requiresProgramConfirmation(
      selected,pkvConfirmed:true,pidConfirmed:false),false);
  });
  test('only configured PID requires a confirmation',(){
    final selected=<String>{'ruzd','pid'};
    expect(WalkParameterSaveRules.requiresProgramConfirmation(
      selected,pkvConfirmed:false,pidConfirmed:false),true);
    expect(WalkParameterSaveRules.requiresProgramConfirmation(
      selected,pkvConfirmed:false,pidConfirmed:true),false);
  });
  test('both programs require both confirmations',(){
    final selected=<String>{'pkv','pid'};
    expect(WalkParameterSaveRules.requiresProgramConfirmation(
      selected,pkvConfirmed:true,pidConfirmed:false),true);
    expect(WalkParameterSaveRules.requiresProgramConfirmation(
      selected,pkvConfirmed:false,pidConfirmed:true),true);
    expect(WalkParameterSaveRules.requiresProgramConfirmation(
      selected,pkvConfirmed:true,pidConfirmed:true),false);
  });
  test('historical captured parameters are immutable',(){
    final padSelected=<String>{'choke','tuzd','ruzd'};
    final snapshot=WalkParameterSaveRules.capturedParameters(padSelected);
    padSelected.add('pkv');
    expect(snapshot,['choke','ruzd','tuzd']);
    expect(()=>snapshot.add('pid'),throwsUnsupportedError);
  });
}
