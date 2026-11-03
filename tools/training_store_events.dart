import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Previous training JSON contains only id/userId/title/date. New properties
/// are optional so old employee records are loaded without a migration.
class TrainingItem {
 const TrainingItem({
   required this.id,required this.userId,required this.title,required this.date,
   this.repeatMonths=12,this.completedAt,this.updatedAt,
 });
 final String id,userId,title;
 final DateTime date;
 final int repeatMonths; // 0 = no recurrence, 6 = half-year, 12 = yearly
 final DateTime? completedAt;
 final DateTime? updatedAt;
 bool get completed=>completedAt!=null;
 TrainingItem copyWith({String? title,DateTime? date,int? repeatMonths,
   DateTime? updatedAt,DateTime? completedAt,bool markComplete=false})=>
   TrainingItem(id:id,userId:userId,title:title??this.title,
      date:date??this.date,repeatMonths:repeatMonths??this.repeatMonths,
      completedAt:markComplete?(completedAt??DateTime.now()):this.completedAt,
      updatedAt:updatedAt??this.updatedAt);
 Map<String,dynamic> toJson()=>{
   'id':id,'userId':userId,'title':title,
   'date':date.toIso8601String(),'repeatMonths':repeatMonths,
   'completedAt':completedAt?.toUtc().toIso8601String(),
   'updatedAt':updatedAt?.toUtc().toIso8601String(),
 };
 static TrainingItem fromJson(Map m)=>TrainingItem(
   id:m['id'].toString(),userId:m['userId'].toString(),
   title:(m['title']??'').toString(),
   date:DateTime.parse(m['date'].toString()),
   repeatMonths:(m['repeatMonths'] as num?)?.toInt()??12,
   completedAt:DateTime.tryParse((m['completedAt']??'').toString()),
   updatedAt:DateTime.tryParse((m['updatedAt']??'').toString()),
 );
}
class TrainingStore extends ChangeNotifier{
 TrainingStore._();
 static final instance=TrainingStore._();
 static const _key='promysel_training_v1',_deletedKey='promysel_training_deleted_v1';
 final List<TrainingItem> items=[];
 final Set<String> deletedIds={};
 bool _loaded=false;
 Future<void> load()async{
   if(_loaded)return;
   _loaded=true;
   final p=await SharedPreferences.getInstance();
   final raw=p.getString(_key);
   if(raw!=null){
     try{
       final arr=jsonDecode(raw) as List;
       items..clear()..addAll(arr.whereType<Map>().map(TrainingItem.fromJson));
     }catch(_){}
   }
   try{
     deletedIds.addAll(((jsonDecode(p.getString(_deletedKey)??'[]')) as List)
       .map((x)=>x.toString()));
   }catch(_){}
   items.removeWhere((x)=>deletedIds.contains(x.id));
   notifyListeners();
 }
 List<TrainingItem> forUser(String id)=>
  (items.where((x)=>x.userId==id).toList()..sort((a,b){
    if(a.completed!=b.completed)return a.completed?1:-1;
    return a.date.compareTo(b.date);
  }));
 List<TrainingItem> onDay(String userId,DateTime day)=>
   forUser(userId).where((x)=>x.date.year==day.year&&
     x.date.month==day.month&&x.date.day==day.day).toList();
 static DateTime nextDate(DateTime from,int months){
   final next=DateTime(from.year,from.month+months);
   final last=DateTime(next.year,next.month+1,0).day;
   return DateTime(next.year,next.month,
     from.day>last?last:from.day);
 }
 Future<void> add(TrainingItem row)async{
   deletedIds.remove(row.id);
   items.removeWhere((x)=>x.id==row.id);
   items.add(row.copyWith(updatedAt:DateTime.now().toUtc()));
   await _save();
   notifyListeners();
 }
 Future<void> update(TrainingItem row)async{
   final i=items.indexWhere((x)=>x.id==row.id&&!deletedIds.contains(x.id));
   if(i<0)throw StateError('Обучение не найдено');
   items[i]=row.copyWith(updatedAt:DateTime.now().toUtc());
   await _save();
   notifyListeners();
 }
 Future<void> completeAndReschedule(TrainingItem row,DateTime date)async{
   final index=items.indexWhere((x)=>x.id==row.id&&!deletedIds.contains(x.id));
   if(index<0)throw StateError('Обучение не найдено');
   if(items[index].completed)throw StateError('Обучение уже отмечено как пройденное');
   final timestamp=DateTime.now().toUtc();
   // Keep completed entry as training history, and add a *new* planned entry.
   items[index]=items[index].copyWith(
     completedAt:timestamp,markComplete:true,updatedAt:timestamp);
   items.add(TrainingItem(
     id:'training_${timestamp.microsecondsSinceEpoch}_${row.id}',
     userId:row.userId,title:row.title,date:date,
     repeatMonths:row.repeatMonths,updatedAt:timestamp,
   ));
   await _save();
   notifyListeners();
 }
 Future<void> remove(String id)async{
   deletedIds.add(id);
   items.removeWhere((x)=>x.id==id);
   await _save();
   notifyListeners();
 }
 Future<void> apply(List raw,{List? remoteDeleted})async{
   if(remoteDeleted!=null)deletedIds.addAll(remoteDeleted.map((x)=>x.toString()));
   final merged=<String,TrainingItem>{
     for(final x in items)if(!deletedIds.contains(x.id))x.id:x,
   };
   for(final value in raw.whereType<Map>()){
     TrainingItem next;
     try{next=TrainingItem.fromJson(value);}catch(_){continue;}
     if(deletedIds.contains(next.id))continue;
     final previous=merged[next.id];
     // Ignore late sync snapshots that would undo a completed/edit operation.
     if(previous==null||!(previous.updatedAt?.isAfter(
       next.updatedAt??DateTime.fromMillisecondsSinceEpoch(0))??false)){
       merged[next.id]=next;
     }
   }
   final newRows=merged.values.toList();
   final before=jsonEncode(items.map((x)=>x.toJson()).toList());
   final after=jsonEncode(newRows.map((x)=>x.toJson()).toList());
   if(before!=after){items..clear()..addAll(newRows);notifyListeners();}
   await _save();
 }
 Future<void> _save()async{
   final p=await SharedPreferences.getInstance();
   await p.setString(_key,jsonEncode(items.map((x)=>x.toJson()).toList()));
   await p.setString(_deletedKey,jsonEncode(deletedIds.toList()));
 }
}
