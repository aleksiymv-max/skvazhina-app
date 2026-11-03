import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:oilman_app/core/services/task_photo_service.dart';
import 'package:oilman_app/features/tasks/task_photo_widgets.dart';

void main(){
  test('Task photos have stable unique UUIDv4 idempotency keys',(){
    final ids=List.generate(100,(_)=>TaskPhotoSelectionController.newId());
    expect(ids.toSet().length,100);
    final format=RegExp(r'^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$');
    expect(ids.every((x)=>format.hasMatch(x)),isTrue);
  });
  testWidgets('Photo picker shows camera, gallery, and optional label',(tester)async{
    final model=TaskPhotoSelectionController();
    await tester.pumpWidget(MaterialApp(home:Scaffold(body:TaskPhotoPicker(photos:model))));
    expect(find.text('Камера'),findsOneWidget);
    expect(find.text('Галерея'),findsOneWidget);
    expect(find.textContaining('фотографии'),findsOneWidget);
    model.dispose();
  });
}
