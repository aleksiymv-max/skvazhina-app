import 'package:flutter_test/flutter_test.dart';
import 'package:oilman_app/core/models/user.dart';
import 'package:oilman_app/core/models/work_task.dart';
import 'package:oilman_app/core/services/task_visibility.dart';

void main() {
  const fieldA='field-aaa',fieldB='field-bbb';
  const chief=AppUser(id:'chief',name:'Chief',role:UserRole.shopChief);
  const master=AppUser(id:'master',name:'Master',role:UserRole.engineer,itrSubrole:ItrSubrole.master);
  const technology=AppUser(id:'tech',name:'Technologist',role:UserRole.engineer,itrSubrole:ItrSubrole.technologist);
  const operator1=AppUser(id:'operator1',name:'Operator 1',role:UserRole.operator);
  const operator2=AppUser(id:'operator2',name:'Operator 2',role:UserRole.operator);
  const otherEngineer=AppUser(id:'engineer2',name:'Engineer 2',role:UserRole.engineer,itrSubrole:ItrSubrole.geologist);
  final workers=<AppUser>[chief,master,technology,operator1,operator2,otherEngineer];
  WorkTask task({String? field=fieldA,String creator='tech',String recipient='operator1',String? completion}){
    return WorkTask(id:'historical-task',title:'Verify pressure',
      description:'Assignment from technologist',createdBy:'Technologist',createdById:creator,
      fieldId:field,createdAt:DateTime(2026,11,5),
      targetType:WorkTaskTarget.personal,targetId:recipient,
      targetName:'Operator 1',completedById:completion,
      status:WorkTaskStatus.confirmed);
  }
  test('chief reads every task only inside own field',(){
    expect(TaskVisibility.canViewHistoryFor(task(),chief,fieldA,workers),true);
    expect(TaskVisibility.canViewHistoryFor(task(field:fieldB),chief,fieldA,workers),false);
  });
  test('master sees technologist assignment to operator and own task',(){
    expect(TaskVisibility.canViewHistoryFor(task(),master,fieldA,workers),true);
    expect(TaskVisibility.canViewHistoryFor(task(creator:'master',recipient:'tech'),master,fieldA,workers),true);
    expect(TaskVisibility.canViewHistoryFor(task(creator:'tech',recipient:'engineer2'),master,fieldA,workers),false);
  });
  test('technologist sees task they issued, not colleague tasks',(){
    expect(TaskVisibility.canViewHistoryFor(task(),technology,fieldA,workers),true);
    expect(TaskVisibility.canViewHistoryFor(task(creator:'engineer2'),technology,fieldA,workers),false);
  });
  test('operator sees own assignment and verified completion, not coworker',(){
    expect(TaskVisibility.canViewHistoryFor(task(),operator1,fieldA,workers),true);
    expect(TaskVisibility.canViewHistoryFor(task(),operator2,fieldA,workers),false);
    expect(TaskVisibility.canViewHistoryFor(task(recipient:'engineer2',completion:'operator2'),operator2,fieldA,workers),true);
  });
  test('unverified historical tasks and foreign fields never become visible',(){
    expect(TaskVisibility.canViewHistoryFor(task(field:null),chief,fieldA,workers),false);
    expect(TaskVisibility.canViewHistoryFor(task(field:fieldB),master,fieldA,workers),false);
    expect(TaskVisibility.canViewHistoryFor(task(field:null),operator1,fieldA,workers),false);
  });
}
