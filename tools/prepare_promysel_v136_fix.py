from pathlib import Path
r=Path.cwd()
def edit(p,f):
 q=r/p;x=q.read_text();q.write_text(f(x))
# Fix v1.36 compile: UserRole import.
edit('lib/features/areas/wells_hierarchy_screen.dart',lambda x: x if "../../core/models/user.dart" in x else x.replace("import 'package:flutter/material.dart';","import 'package:flutter/material.dart';\nimport '../../core/models/user.dart';"))

# Registration: normalize email and use a robust validation expression.
def auth(x):
 x=x.replace("final emailOk=RegExp(r'^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$').hasMatch(email);","final normalizedEmail=email.trim().toLowerCase();\n    final emailOk=RegExp(r'^[^@\\s]+@[^@\\s]+\\.[^@\\s]{2,}$').hasMatch(normalizedEmail);")
 x=x.replace("final emailOk = RegExp(r'^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$').hasMatch(email);","final normalizedEmail=email.trim().toLowerCase();\n    final emailOk=RegExp(r'^[^@\\s]+@[^@\\s]+\\.[^@\\s]{2,}$').hasMatch(normalizedEmail);")
 x=x.replace("email:email.trim()","email:normalizedEmail")
 x=x.replace("email: email.trim()","email: normalizedEmail")
 return x
for p in ['lib/features/auth/auth_screen.dart','lib/features/auth/register_screen.dart','lib/features/auth/registration_screen.dart']:
 q=r/p
 if q.exists(): edit(p,auth)
