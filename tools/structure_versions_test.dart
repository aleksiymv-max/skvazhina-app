import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:oilman_app/core/models/production_area.dart';
import 'package:oilman_app/core/models/pad.dart';
import 'package:oilman_app/core/models/well.dart';
import 'package:oilman_app/core/models/user.dart';
import 'package:oilman_app/core/services/app_state_store.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  SharedPreferences.setMockInitialValues({});
  final state=AppStateStore.instance;
  setUp(() { demoAreas.clear(); demoPads.clear(); });

  test('shop chief can edit and delete; ITR cannot delete', () {
    const chief=AppUser(id:'chief',name:'Chief',role:UserRole.shopChief);
    const itr=AppUser(id:'engineer',name:'Engineer',role:UserRole.engineer,
      itrSubrole:ItrSubrole.leadingGeologist);
    expect(chief.canCreateStructure,isTrue);
    expect(chief.canEditStructure,isTrue);
    expect(chief.canDeleteStructure,isTrue);
    expect(itr.canEditStructure,isTrue);
    expect(itr.canDeleteStructure,isFalse);
  });

  test('renamed area survives an older snapshot from another phone', () {
    const field='test-hierarchy-versions-area-v195';
    final area=ProductionArea(id:'area-v195',name:'Before',padIds:[],fieldId:field);
    demoAreas.add(area);
    final stale=state.snapshot(field);
    area.name='After';
    state.touchStructure(field,'areas',area.id);
    final merged=state.reconcileWithCurrent(field,stale);
    expect(((merged['areas'] as List).single as Map)['name'],'After');
  });

  test('renamed well survives an old pad snapshot', () {
    const field='test-hierarchy-versions-well-v195';
    final area=ProductionArea(id:'area-well-v195',name:'Section',padIds:['pad-v195'],fieldId:field);
    final pad=Pad(id:'pad-v195',name:'Pad',type:'Oil',areaId:area.id,areaName:area.name,fieldId:field,
      wells:[Well(id:'well-v195',number:'100',type:WellType.oil,status:WellStatus.working)]);
    demoAreas.add(area);demoPads.add(pad);
    final stale=state.snapshot(field);
    pad.wells[0]=Well(id:'well-v195',number:'101',type:WellType.oil,status:WellStatus.working);
    state.touchStructure(field,'wells','well-v195');
    final merged=state.reconcileWithCurrent(field,stale);
    final wells=((merged['pads'] as List).single as Map)['wells'] as List;
    expect((wells.single as Map)['number'],'101');
  });
}
