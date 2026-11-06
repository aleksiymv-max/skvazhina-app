#!/usr/bin/env python3
"""One-shot read-only inspection of generated walk, home, router and problem models."""
from pathlib import Path
import re

root=Path("lib")
paths=[
"features/walk/walk_start_screen.dart",
"features/walk/walk_screen.dart",
"features/walk/walk_area_screen.dart",
"features/walk/walk_summary_screen.dart",
"features/home/home_screen.dart",
"features/menu/menu_screen.dart",
"app/app.dart",
"core/models/measurement.dart",
"core/models/production_area.dart",
"core/models/well.dart",
"core/models/pad.dart",
"core/repositories/measurement_repository.dart",
"core/services/repository.dart",
"core/services/sync_service.dart",
"core/database/app_database.dart",
"core/services/session_service.dart"
]
for sub in paths:
    file=root/sub
    if not file.exists():print("NOT_FOUND",sub);continue
    content=file.read_text(encoding="utf-8")
    print("FILE",sub,"bytes",len(content))
    if sub in ("features/walk/walk_start_screen.dart","features/walk/walk_screen.dart","features/walk/walk_area_screen.dart","features/home/home_screen.dart","features/menu/menu_screen.dart"):
        print("FIRST",content[:11500])
        keys=["Widget build(", "_showProblems(", "_load()", "Widget _problemsDashboard", "Future<void> _load(", "Widget _show", "ListView("]
        for key in keys:
            pos=content.find(key)
            if pos>=0:print("EXCERPT",key,content[max(0,pos-650):pos+9500])
    elif sub=="app/app.dart":print("ROUTER",content[:14000])
    elif sub.startswith("core/models/"):
        print("MODEL",content[:11000])
    elif "repository" in sub:print("REPOSITORY",content[:17000])
    else:
        needles=["unresolvedProblems(", "saveMeasurement(", "save(", "operatorName", "recordMeasurement(", "Future<void> syncNow", "List<ProductionArea>","List<Pad>","currentUser", "currentFieldId"]
        for key in needles:
            pos=content.find(key)
            if pos>=0:print("HIT",key,content[max(pos-300,0):pos+3500])
print("INSPECTION_FINISHED")
