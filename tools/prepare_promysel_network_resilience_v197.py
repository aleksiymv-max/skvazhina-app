#!/usr/bin/env python3
"""V1.97: bound repeated read-only network work on unreachable links.

Executed after all previous shared Flutter source transforms. Mutating calls,
auth decisions, cached offline measurements and sync idempotency are unchanged.
"""
from pathlib import Path

p=Path('lib/core/network/weak_network.dart')
s=p.read_text(encoding='utf-8')
a='class WeakNetwork {\n  WeakNetwork._();'
b='''class WeakNetwork {
  WeakNetwork._();
  // Per-isolate short circuit only after repeated socket/time-out failures.
  // An HTTP 401/403/500 is proof the server is reachable and never triggers it.
  static int _transportFailures=0;
  static DateTime? _transportCooldown;
  static bool get _coolingDown=>_transportCooldown!=null&&
      DateTime.now().isBefore(_transportCooldown!);
  static void _transportFailed(){
    _transportFailures++;
    if(_transportFailures>=2){
      _transportCooldown=DateTime.now().add(const Duration(seconds:12));
      _transportFailures=0;
    }
  }
  static void _transportReached(){
    _transportFailures=0;
    _transportCooldown=null;
  }'''
assert s.count(a)==1, 'WeakNetwork class anchor modified'
s=s.replace(a,b,1)
a='''    assert(attempts >= 1 && attempts <= 3);
    for (var i = 0; i < attempts; i++) {'''
b='''    assert(attempts >= 1 && attempts <= 3);
    if(_coolingDown)throw http.ClientException(
      'Сервер временно недоступен из этой сети. Локальные данные сохранены.');
    for (var i = 0; i < attempts; i++) {'''
assert s.count(a)==1,'retry anchor modified'
s=s.replace(a,b,1)
a='''        if (i + 1 == attempts || !retryableStatus(result.statusCode)) {
          return result;
        }
      } on TimeoutException {
        if (i + 1 == attempts) rethrow;
      } on http.ClientException {
        if (i + 1 == attempts) rethrow;
      }'''
b='''        if (i + 1 == attempts || !retryableStatus(result.statusCode)) {
          _transportReached();
          return result;
        }
      } on TimeoutException {
        if (i + 1 == attempts){_transportFailed();rethrow;}
      } on http.ClientException {
        if (i + 1 == attempts){_transportFailed();rethrow;}
      }'''
assert s.count(a)==1,'retry error flow modified'
s=s.replace(a,b,1)
p.write_text(s,encoding='utf-8')

# Non-mutating periodic synchronization should not stall the network queue for
# nearly a minute when DNS/SNI connectivity fails on a weak mobile link.
p=Path('lib/core/services/sync_service.dart')
s=p.read_text(encoding='utf-8')
a='timeout:const Duration(seconds:25),attempts:2'
b='timeout:const Duration(seconds:12),attempts:2'
assert s.count(a)==1,'sync read timeout anchor changed'
p.write_text(s.replace(a,b,1),encoding='utf-8')

# A sign-in timeout should be actionable and still allow slow HTTPS handshakes.
# Do not retry POST /auth/login: it could create duplicate sessions.
p=Path('lib/core/services/registration_service.dart')
s=p.read_text(encoding='utf-8')
assert 'One attempt per tap: retrying credentials can open extra sessions.' in s
print('PASS network resilience: bounded GET retries, short transport cooldown, no POST replay')
