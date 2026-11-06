#!/usr/bin/env python3
"""Integrate About into the FINAL menu, after v1.80-v1.88 menu transforms.
Avoids breaking legacy patch hunks that must match the original template.
"""
from pathlib import Path
p=Path("lib/features/menu/menu_screen.dart")
s=p.read_text(encoding="utf-8")
top="import 'package:flutter/material.dart';\n"
assert s.count(top)==1, "About import anchor missing"
assert "import 'about_screen.dart';" not in s
s=s.replace(top,top+"import 'about_screen.dart';\n",1)
anchor="  ]))),"
assert s.count(anchor)==1, "Expected avatar-aware v1.84 menu layout"
item="""   const SizedBox(height:8),
   Card(
     margin:const EdgeInsets.only(bottom:10),
     child:ListTile(
       contentPadding:const EdgeInsets.symmetric(horizontal:16,vertical:5),
       leading:const Icon(Icons.info_outline,size:26),
       title:const Text('О приложении',
         style:TextStyle(fontWeight:FontWeight.w700)),
       subtitle:const Text('О системе, руководство, история версий, сервер'),
       trailing:const Icon(Icons.chevron_right),
       onTap:()=>Navigator.of(context).push(MaterialPageRoute<void>(
         builder:(_)=>const PromyselAboutScreen())),
     ),
   ),
"""
s=s.replace(anchor,item+anchor,1)
assert s.count("PromyselAboutScreen()")==1
p.write_text(s,encoding="utf-8")
assert Path("lib/features/menu/about_screen.dart").exists()
print("PASS v2.15: About entry added after all legacy menu patches")
