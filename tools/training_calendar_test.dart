import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:oilman_app/core/services/training_store.dart';
import 'package:oilman_app/core/services/work_schedule_store.dart';

void main(){
 TestWidgetsFlutterBinding.ensureInitialized();
 SharedPreferences.setMockInitialValues({});
 const uid='test-training-calendar-user';
 final training=TrainingStore.instance;
 final schedule=WorkScheduleStore.instance;
 test('annual and half-year recurrence uses calendar months',(){
   expect(TrainingStore.nextDate(DateTime(2026,8,31),6),DateTime(2027,2,28));
   expect(TrainingStore.nextDate(DateTime(2026,2,28),12),DateTime(2027,2,28));
   expect(TrainingStore.nextDate(DateTime(2026,10,15),6),DateTime(2027,4,15));
 });
 test('complete training preserves history and schedules next event',()async{
   await training.load();
   const id='test-recurring-training-original';
   await training.add(TrainingItem(
     id:id,userId:uid,title:'Промышленная безопасность',
     date:DateTime(2026,11,20),repeatMonths:6,
   ));
   final original=training.forUser(uid).singleWhere((x)=>x.id==id);
   await training.completeAndReschedule(original,DateTime(2027,5,21));
   final entries=training.forUser(uid);
   expect(entries.length,2);
   expect(entries.singleWhere((x)=>x.id==id).completed,true);
   final future=entries.singleWhere((x)=>!x.completed);
   expect(future.title,original.title);
   expect(future.repeatMonths,6);
   expect(future.date,DateTime(2027,5,21));
   expect(training.onDay(uid,DateTime(2027,5,21)).length,1);
   expect(training.onDay('another-user',DateTime(2027,5,21)),isEmpty);
 });
 test('outdated snapshot cannot undo completed training',()async{
   final previous=TrainingItem(
     id:'test-recurring-training-original',userId:uid,
     title:'Промышленная безопасность',date:DateTime(2026,11,20));
   await training.apply([previous.toJson()]);
   expect(training.forUser(uid).where((x)=>x.id==previous.id).single.completed,true);
 });
 test('training removal tombstones remain effective',()async{
   final row=training.forUser(uid).firstWhere((x)=>!x.completed);
   await training.remove(row.id);
   await training.apply([row.toJson()]);
   expect(training.forUser(uid).where((x)=>x.id==row.id),isEmpty);
 });
 test('month editor only updates chosen day and splits vacation range',()async{
   await schedule.ensureLoaded();
   await schedule.change(uid,(s){
     s.arrival=DateTime(2026,10,15);
     s.leave.add(SchedulePeriod(
       start:DateTime(2026,11,29),
       end:DateTime(2026,12,3),type:'leave'));
   });
   await schedule.setDayStatus(uid,DateTime(2026,11,30),'work');
   expect(schedule.status(uid,DateTime(2026,11,29)),'leave');
   expect(schedule.status(uid,DateTime(2026,11,30)),'work');
   expect(schedule.status(uid,DateTime(2026,12,1)),'leave');
   expect(schedule.status(uid,DateTime(2026,12,3)),'leave');
   await schedule.setDayStatus(uid,DateTime(2026,11,30),'reset');
   expect(schedule.status(uid,DateTime(2026,11,30)),'rest');
   expect(schedule.status(uid,DateTime(2026,12,1)),'leave');
   await schedule.setDayStatus(uid,DateTime(2026,12,1),'rest');
   expect(schedule.status(uid,DateTime(2026,12,1)),'rest');
   expect(schedule.status(uid,DateTime(2026,12,2)),'leave');
 });
}
