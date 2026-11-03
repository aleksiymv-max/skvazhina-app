import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:oilman_app/core/services/work_schedule_store.dart';

void main(){
  TestWidgetsFlutterBinding.ensureInitialized();
  SharedPreferences.setMockInitialValues({});
  final store=WorkScheduleStore.instance;
  test('month on month off follows arrival, not 30-day blocks',()async{
    await store.change('shift-test',(s)=>s.arrival=DateTime(2026,10,15));
    expect(store.status('shift-test',DateTime(2026,10,15)),'work');
    expect(store.status('shift-test',DateTime(2026,11,14)),'work');
    expect(store.status('shift-test',DateTime(2026,11,15)),'rest');
    expect(store.status('shift-test',DateTime(2026,12,14)),'rest');
    expect(store.status('shift-test',DateTime(2026,12,15)),'work');
  });
  test('independent split leave portions override regular rotation',()async{
    await store.change('shift-test',(s){
      s.leave.add(SchedulePeriod(start:DateTime(2026,10,21),
        end:DateTime(2026,10,25),type:'leave'));
      s.leave.add(SchedulePeriod(start:DateTime(2026,12,17),
        end:DateTime(2026,12,28),type:'leave'));
    });
    expect(store.status('shift-test',DateTime(2026,10,22)),'leave');
    expect(store.status('shift-test',DateTime(2026,12,20)),'leave');
    expect(store.status('shift-test',DateTime(2026,12,29)),'work');
  });
  test('exceptional autumn swap overrides shift cycle',()async{
    await store.change('shift-test',(s){
      s.overrides.add(SchedulePeriod(start:DateTime(2026,11,16),
        end:DateTime(2026,11,30),type:'work'));
    });
    expect(store.status('shift-test',DateTime(2026,11,20)),'work');
    expect(store.status('shift-test',DateTime(2026,12,1)),'rest');
  });
  test('other users do not inherit a colleague schedule',(){
    expect(store.status('other-employee',DateTime(2026,11,20)),'unset');
  });
}
