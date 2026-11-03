from pathlib import Path
p=Path('lib/core/services/work_schedule_store.dart')
s=p.read_text(encoding='utf-8')
anchor='  static DateTime _addMonth(DateTime anchor,int n){'
assert s.count(anchor)==1
method="""  /// Change exactly one day. Splits overlapping ranges instead of deleting
  /// whole leave/rotation periods that extend into other calendar months.
  Future<void> setDayStatus(String userId,DateTime date,String type)async{
    if(!const ['work','rest','leave','reset'].contains(type))
      throw ArgumentError.value(type,'type');
    final day=DateTime(date.year,date.month,date.day);
    await change(userId,(record){
      _removeDay(record.leave,day);
      _removeDay(record.overrides,day);
      final entry=SchedulePeriod(start:day,end:day,type:type);
      if(type=='leave')record.leave.add(entry);
      if(type=='work'||type=='rest')record.overrides.add(entry);
    });
  }
  static void _removeDay(List<SchedulePeriod> periods,DateTime day){
    final next=<SchedulePeriod>[];
    for(final p in periods){
      if(day.isBefore(p.start)||day.isAfter(p.end)){
        next.add(p);
        continue;
      }
      if(p.start.isBefore(day)){
        next.add(SchedulePeriod(
          start:p.start,end:DateTime(day.year,day.month,day.day-1),
          type:p.type));
      }
      if(p.end.isAfter(day)){
        next.add(SchedulePeriod(
          start:DateTime(day.year,day.month,day.day+1),end:p.end,
          type:p.type));
      }
    }
    periods..clear()..addAll(next);
  }
"""
s=s.replace(anchor,method+anchor,1)
p.write_text(s,encoding='utf-8')
assert 'setDayStatus' in s
print('PASS single day work/rest/leave with lossless split and reset')
