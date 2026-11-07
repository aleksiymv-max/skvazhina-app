#!/usr/bin/env python3
"""Read-only generated source diagnostics for home sync and chat playback."""
from pathlib import Path
import re
def show(file,anchors,limit=2400):
 s=Path(file).read_text()
 print("###FILE",file,"LEN",len(s))
 for a in anchors:
  p=s.find(a)
  print("###ANCHOR",repr(a),"POS",p)
  if p>=0: print(s[max(0,p-250):p+limit])
show('lib/features/home/home_screen.dart',[
 'void initState()','Future<void> _load()', 'Future<void> _refreshProblemSnapshot()',
 'Widget _statusDashboard','Widget _problemsDashboard','_showProblems()',
 'allWellStatuses()', 'unresolvedProblems()', 'void _syncChanged()'],2200)
show('lib/core/database/app_database.dart',[
 'Future<void> resolveProblem(', 'Future<void> updateWellStatus(',
 'Future<void> applyRemoteMeasurement(', 'Future<Map<String,WellStatus>> allWellStatuses(',
 'Future<void> saveWellStatus(', 'Future<void> updateProblem'],2500)
show('lib/core/repositories/measurement_repository.dart',[
 'Future<void> resolveProblem(', 'Future<Map<String,WellStatus>> allWellStatuses('],1800)
show('lib/core/services/sync_service.dart',[
 'Future<void> syncNow(', 'Future<void> _pull()async{',
 'if(latestState!=null)', 'reconcileWithCurrent', 'if(_stateDirty)', 'Future<void> _pushState()async{',
 'Future<void> _applyDomain', '_lastState'],2800)
show('lib/features/chat/promysel_chat_screen.dart',[
 'void _refresh(', "kind=='video_note'", 'ChatVideoMedia(', '_visibleVideos',
 'Future<void> _loadVideo(', 'Future<void> _sendVideoNote('],2200)
show('lib/core/services/promysel_chat_service.dart',[
 'Future<List<Map<String,dynamic>>> messages(', 'Future<List<Map<String,dynamic>>> rooms(', 'Future<void> sendMedia(', 'VideoPlayer'],1700)
