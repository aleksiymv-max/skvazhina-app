import 'package:flutter_test/flutter_test.dart';
import 'package:oilman_app/core/models/user.dart';
import 'package:oilman_app/core/models/work_task.dart';
import 'package:oilman_app/core/services/task_visibility.dart';

void main() {
  const fieldId='field-review-209';
  const chief=AppUser(id:'chief-209',name:'Начальник',role:UserRole.shopChief);
  const worker=AppUser(id:'worker-209',name:'Оператор',role:UserRole.operator);

  WorkTask newTask()=>WorkTask(
    id:'task-review-209',
    title:'Проверить параметры скважины',
    description:'Учебное задание без обращения к серверу',
    createdBy:chief.name,createdById:chief.id,
    fieldId:fieldId,
    createdAt:DateTime.utc(2026,11,5),
    targetType:WorkTaskTarget.personal,
    targetId:worker.id,targetName:worker.name,
  );

  test('completion creates pending approval, only confirmation moves task to history',() {
    final task=newTask();
    final store=WorkTaskStore.instance;
    expect(task.status,WorkTaskStatus.active);
    expect(store.complete(task,worker.name,userId:worker.id),isTrue);
    expect(task.status,WorkTaskStatus.awaitingConfirmation);
    expect(task.status!=WorkTaskStatus.confirmed,isTrue);

    expect(store.confirm(task,userId:'other',userName:'Чужой',isShopChief:false),isFalse);
    expect(task.status,WorkTaskStatus.awaitingConfirmation);

    expect(store.confirm(task,userId:chief.id,userName:chief.name,isShopChief:true),isTrue);
    expect(task.status,WorkTaskStatus.confirmed);
    expect(task.status!=WorkTaskStatus.confirmed,isFalse);
    expect(TaskVisibility.canViewHistoryFor(task,chief,fieldId,[chief,worker]),isTrue);
    expect(TaskVisibility.canViewHistoryFor(task,worker,fieldId,[chief,worker]),isTrue);
    expect(TaskVisibility.canViewHistoryFor(task,chief,'other-field',[chief,worker]),isFalse);
  });

  test('rejection returns pending task to active work, not history',() {
    final task=newTask();
    final store=WorkTaskStore.instance;
    expect(store.complete(task,worker.name,userId:worker.id),isTrue);
    expect(store.reject(task,userId:chief.id,userName:chief.name,comment:'Повторить замер',isShopChief:true),isTrue);
    expect(task.status,WorkTaskStatus.active);
    expect(task.status!=WorkTaskStatus.confirmed,isTrue);
  });
}
