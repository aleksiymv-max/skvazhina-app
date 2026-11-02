import 'package:flutter_test/flutter_test.dart';
import 'package:oilman_app/core/models/work_task.dart';

WorkTask newTask(String id) => WorkTask(
  id: id,
  title: 'Проверка',
  description: 'Только синтетические данные',
  createdBy: 'Автор',
  createdById: 'author-1',
  createdAt: DateTime.utc(2026, 1, 1),
  targetType: WorkTaskTarget.personal,
  targetId: 'worker-1',
  targetName: 'Сотрудник',
  status: WorkTaskStatus.awaitingConfirmation,
);

void main() {
  test('Чужой сотрудник не может подтвердить задание', () {
    final task = newTask('permission-confirm');
    expect(WorkTaskStore.instance.confirm(task,
      userId: 'other-1', userName: 'Посторонний', isShopChief: false), isFalse);
    expect(task.status, WorkTaskStatus.awaitingConfirmation);
    expect(WorkTaskStore.instance.confirm(task,
      userId: 'author-1', userName: 'Автор', isShopChief: false), isTrue);
    expect(task.status, WorkTaskStatus.confirmed);
  });

  test('Чужой сотрудник не может отклонить задание', () {
    final task = newTask('permission-reject');
    expect(WorkTaskStore.instance.reject(task,
      userId: 'other-1', userName: 'Посторонний', comment: 'Нет', isShopChief: false), isFalse);
    expect(task.status, WorkTaskStatus.awaitingConfirmation);
    expect(WorkTaskStore.instance.reject(task,
      userId: 'author-1', userName: 'Автор', comment: 'Исправить', isShopChief: false), isTrue);
    expect(task.status, WorkTaskStatus.active);
  });

  test('Начальник может подтвердить или отклонить', () {
    final task = newTask('permission-chief');
    expect(WorkTaskStore.instance.reject(task,
      userId: 'chief-1', userName: 'Начальник', comment: 'Доработать', isShopChief: true), isTrue);
    task.status = WorkTaskStatus.awaitingConfirmation;
    expect(WorkTaskStore.instance.confirm(task,
      userId: 'chief-1', userName: 'Начальник', isShopChief: true), isTrue);
  });
}
