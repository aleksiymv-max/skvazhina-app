"""Install platform Badging API bridge into generated iPhone PWA index.html.
Only installed iOS/iPadOS Home Screen web apps with notification permission
will actually show the icon badge. No background push is claimed.
"""
from pathlib import Path
p=Path.cwd()/'web/index.html'
s=p.read_text(encoding='utf-8')
assert '</head>' in s and 'promyselUpdateAppBadge' not in s
script="""<script>
window.promyselBadgeCount = 0;
window.promyselUpdateAppBadge = function(count) {
  const n = Math.max(0, Math.floor(Number(count) || 0));
  window.promyselBadgeCount = n;
  if (n > 0 && typeof navigator.setAppBadge === 'function') {
    try { const p = navigator.setAppBadge(n); if (p && p.catch) p.catch(() => {}); } catch (_) {}
  } else if (n === 0 && typeof navigator.clearAppBadge === 'function') {
    try { const p = navigator.clearAppBadge(); if (p && p.catch) p.catch(() => {}); } catch (_) {}
  }
};
window.promyselRequestBadgePermission = function() {
  if (typeof Notification === 'undefined' ||
      typeof Notification.requestPermission !== 'function') return;
  if (Notification.permission !== 'default') {
    window.promyselUpdateAppBadge(window.promyselBadgeCount);
    return;
  }
  try {
    const p = Notification.requestPermission();
    if (p && p.then) p.then(() => window.promyselUpdateAppBadge(window.promyselBadgeCount)).catch(() => {});
  } catch (_) {}
};
</script>
"""
s=s.replace('</head>',script+'</head>',1)
p.write_text(s,encoding='utf-8')
assert s.count('promyselUpdateAppBadge')>=3
print('PASS: iPhone Home Screen PWA app icon Badging API bridge')
