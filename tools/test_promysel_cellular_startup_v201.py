#!/usr/bin/env python3
"""Post-build regression check for Russian-cellular startup on Tuqo."""
from pathlib import Path
import re,subprocess,tempfile

r=Path('build/web')
s=(r/'flutter_bootstrap.js').read_text()
index=(r/'index.html').read_text()
worker=(r/'promysel-push-sw.js').read_text()
diag=(r/'diagnostics.html').read_text()
checks={
 'engine forced to local origin': 'canvasKitBaseUrl:"/canvaskit/"' in s and 'useLocalCanvasKit:true' in s,
 'local CanvasKit files bundled': (r/'canvaskit/canvaskit.wasm').stat().st_size>1000000 and (r/'canvaskit/canvaskit.js').exists(),
 'app loader ready with retry': all(x in index for x in ['id="promysel-startup"','Проверить подключение','flutter-first-frame','location.reload()']),
 'early main JS preload': 'href="/main.dart.js" as="script"' in index,
 'public-only cache': "url.origin!==self.location.origin" in worker and "path.startsWith('/canvaskit/')" in worker and "path.startsWith('/assets/')" in worker,
 'no auth/chat cached': "path.startsWith('/functions/')" not in worker and "promysel-chat" not in worker,
 'device diagnostics include Supabase': 'promysel-compat/health' in diag and 'HEAD' in diag,
 'all files in Web root': (r/'index.html').exists() and (r/'main.dart.js').exists() and (r/'sqlite3.wasm').exists(),
}
for label,ok in checks.items():print(('PASS' if ok else 'FAIL')+' mobile-startup '+label)
assert all(checks.values())

# Smoke-check all emitted scripts with the runner's real Node JS parser.
with tempfile.TemporaryDirectory() as temp:
 for name in ['flutter_bootstrap.js','promysel-push-sw.js']:
  subprocess.run(['node','--check',str(r/name)],check=True)
 for name,source in [('index.html',index),('diagnostics.html',diag)]:
  for n,match in enumerate(re.findall(r'<script(?:\s+[^>]*)?>([\s\S]*?)</script>',source)):
   p=Path(temp)/(name.replace('.html','')+f'-{n}.js')
   p.write_text(match)
   subprocess.run(['node','--check',str(p)],check=True)
print('PASS v2.01: browsers can parse startup scripts; all critical resources local; no API data cached')
