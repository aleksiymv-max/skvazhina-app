import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// A month on / month off cycle anchored at the day of arrival. Offsets are
/// calculated in calendar months, not fixed 30-day periods. Manual work/rest
/// ranges handle exceptional shift swaps (including autumn adjustments).
class SchedulePeriod {
  const SchedulePeriod({required this.start,required this.end,required this.type});
  final DateTime start,end;
  final String type; // work, rest or leave
  Map<String,dynamic> toJson()=>{'start':_ymd(start),'end':_ymd(end),'type':type};
  static SchedulePeriod fromJson(Map x)=>SchedulePeriod(
    start:DateTime.parse(x['start'].toString()),
    end:DateTime.parse(x['end'].toString()),
    type:x['type'].toString());
  static String _ymd(DateTime d)=>'${d.year.toString().padLeft(4,'0')}-${d.month.toString().padLeft(2,'0')}-${d.day.toString().padLeft(2,'0')}';
}
class EmployeeSchedule {
  EmployeeSchedule({this.arrival, List<SchedulePeriod>? overrides,List<SchedulePeriod>? leave,DateTime? updated})
   :overrides=overrides??[],leave=leave??[],updated=updated??DateTime.fromMillisecondsSinceEpoch(0);
  DateTime? arrival;
  final List<SchedulePeriod> overrides,leave;
  DateTime updated;
  Map<String,dynamic> toJson()=>{
    'arrival':arrival==null?null:SchedulePeriod._ymd(arrival!),
    'overrides':overrides.map((x)=>x.toJson()).toList(),
    'leave':leave.map((x)=>x.toJson()).toList(),
    'updated':updated.toUtc().toIso8601String(),
  };
  static EmployeeSchedule fromJson(Map x)=>EmployeeSchedule(
    arrival:DateTime.tryParse((x['arrival']??'').toString()),
    overrides:(x['overrides'] as List? ??[]).whereType<Map>().map(SchedulePeriod.fromJson).toList(),
    leave:(x['leave'] as List? ??[]).whereType<Map>().map(SchedulePeriod.fromJson).toList(),
    updated:DateTime.tryParse((x['updated']??'').toString()),
  );
}
class WorkScheduleStore extends ChangeNotifier {
  WorkScheduleStore._();
  static final instance=WorkScheduleStore._();
  final Map<String,EmployeeSchedule> entries={};
  bool _loaded=false;
  static String _date(DateTime d)=>SchedulePeriod._ymd(d);
  EmployeeSchedule forUser(String id)=>entries[id]??EmployeeSchedule();
  Map<String,dynamic> snapshot()=>entries.map((id,value)=>MapEntry(id,value.toJson()));
  Future<void> ensureLoaded()async{
    if(_loaded)return;_loaded=true;
    final p=await SharedPreferences.getInstance();
    final raw=p.getString('promysel_work_schedules_v1');
    if(raw==null)return;
    try{
      final parsed=jsonDecode(raw);
      if(parsed is Map){
        for(final e in parsed.entries){
          if(e.value is Map)entries[e.key.toString()]=EmployeeSchedule.fromJson(e.value);
        }
      }
    }catch(_){}
    notifyListeners();
  }
  Future<void> apply(Map remote)async{
    var changed=false;
    for(final e in remote.entries){
      if(e.value is! Map)continue;
      final parsed=EmployeeSchedule.fromJson(e.value);
      final key=e.key.toString(),current=entries[key];
      if(current==null||parsed.updated.isAfter(current.updated)){
        entries[key]=parsed;changed=true;
      }
    }
    if(changed){await _save();notifyListeners();}
  }
  Future<void> _save()async{
    final p=await SharedPreferences.getInstance();
    await p.setString('promysel_work_schedules_v1',jsonEncode(snapshot()));
  }
  Future<void> change(String userId,void Function(EmployeeSchedule) edit)async{
    final v=forUser(userId);
    edit(v);
    v.updated=DateTime.now().toUtc();
    entries[userId]=v;
    await _save();notifyListeners();
  }
  static DateTime _addMonth(DateTime anchor,int n){
    final first=DateTime(anchor.year,anchor.month+n);
    final last=DateTime(first.year,first.month+1,0).day;
    return DateTime(first.year,first.month,anchor.day>last?last:anchor.day);
  }
  String status(String userId,DateTime date){
    final day=DateTime(date.year,date.month,date.day);
    final schedule=forUser(userId);
    // Leave takes precedence over swaps and regular rotation.
    for(final period in schedule.leave){
      if(!day.isBefore(period.start)&&!day.isAfter(period.end))return 'leave';
    }
    for(final period in schedule.overrides.reversed){
      if(!day.isBefore(period.start)&&!day.isAfter(period.end))return period.type;
    }
    final anchor=schedule.arrival;
    if(anchor==null||day.isBefore(anchor))return 'unset';
    int months=(day.year-anchor.year)*12+day.month-anchor.month;
    while(months>0&&day.isBefore(_addMonth(anchor,months)))months--;
    while(!day.isBefore(_addMonth(anchor,months+1)))months++;
    return months.isEven?'work':'rest';
  }
}
