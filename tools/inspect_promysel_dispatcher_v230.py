#!/usr/bin/env python3
"""Read only current generated home, roles and legacy dispatch service."""
from pathlib import Path
def section(path,start,end=None,maxn=24000):
 s=Path(path).read_text(encoding='utf-8')
 p=s.find(start)
 if p<0: print('NOT FOUND',path,start);return
 q=s.find(end,p+len(start)) if end else min(len(s),p+maxn)
 if q<0:q=min(len(s),p+maxn)
 print('##',path,'from',repr(start),'bytes',q-p)
 print(s[p:q][:maxn])
section('lib/features/home/home_screen.dart',' Future<void> _showProblems() async {','  Widget _standaloneProblemCard',22000)
section('lib/features/home/home_screen.dart',' Widget _standaloneProblemCard','\n}',11000)
section('lib/core/services/problem_application_store.dart','class ProblemApplicationStore',None,11000)
section('lib/core/models/user.dart','enum UserRole',None,5800)
section('lib/core/models/measurement.dart','class Measurement',None,6200)
section('lib/core/services/session_service.dart','class SessionService',None,2800)
