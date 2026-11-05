import 'package:flutter_test/flutter_test.dart';
import 'package:oilman_app/core/services/structure_tombstones.dart';

void main() {
  test('deleting an area removes area, its pads and wells but not other areas', () {
    final old = <String, dynamic>{
      'areas': [
        {'id':'a1','name':'Участок','padIds':['p1','p2']},
        {'id':'a2','name':'Другой','padIds':['p3']}
      ],
      'pads': [
        {'id':'p1','areaId':'a1','wells':[{'id':'w1'}]},
        {'id':'p2','areaId':'a1','wells':[{'id':'w2'}]},
        {'id':'p3','areaId':'a2','wells':[{'id':'w3'}]}
      ],
      'structureDeleted': {'areas':['a1'],'pads':['p1','p2'],'wells':['p1:w1','p2:w2']},
    };
    final r = StructureTombstones.filter(old);
    expect((r['areas'] as List).map((e)=>e['id']),['a2']);
    expect((r['pads'] as List).map((e)=>e['id']),['p3']);
    expect((r['pads'] as List).single['wells'][0]['id'],'w3');
  });

  test('old offline snapshot cannot resurrect deleted pad/well', () {
    final deleted = {'areas':<String>[],'pads':['p1'],'wells':['p2:w2']};
    final stale = {'areas':<String>[],'pads':<String>[],'wells':<String>[]};
    final markers = StructureTombstones.merge(deleted,stale);
    final result = StructureTombstones.filter({
      'areas':[{'id':'a1','padIds':['p1','p2']}],
      'pads':[{'id':'p1','areaId':'a1','wells':[{'id':'w1'}]},
              {'id':'p2','areaId':'a1','wells':[{'id':'w2'},{'id':'w3'}]}],
      'structureDeleted':markers,
    });
    expect((result['pads'] as List).length,1);
    expect((result['pads'] as List).single['wells'].map((e)=>e['id']),['w3']);
    expect((result['areas'] as List).single['padIds'],['p2']);
  });

  test('field marker merge deduplicates and keeps earlier deletions', () {
    final first={'areas':['a1'],'pads':['p1'],'wells':<String>[]};
    final second={'areas':['a1','a2'],'pads':<String>[],'wells':['w1']};
    expect(StructureTombstones.merge(first,second),{
      'areas':['a1','a2'],'pads':['p1'],'wells':['w1']
    });
  });

  test('empty markers do not hide valid structure', () {
    final structure={'areas':[{'id':'a1','padIds':['p1']}],
      'pads':[{'id':'p1','areaId':'a1','wells':[{'id':'w1'}]}]};
    final result=StructureTombstones.filter(structure);
    expect((result['areas'] as List).length,1);
    expect((result['pads'] as List).length,1);
    expect((result['pads'] as List).single['wells'].length,1);
  });
}
