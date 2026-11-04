#!/usr/bin/env python3
"""Prepare a Cloudflare-independent, same-origin Flutter Web release.

The resulting frontend calls /functions/v1, /auth/v1, /storage/v1 etc.
on its own public domain. Nginx proxies them to the existing Supabase project.
All server keys and existing database contents remain unchanged.
"""
import argparse
import shutil
from pathlib import Path

UPSTREAM = 'https://xptmcufhuvtcunqzlsme.supabase.co'
SUPPORTED = {'.js', '.html', '.json', '.css', '.webmanifest'}


def prepare(src: Path, dest: Path) -> dict:
    src = src.resolve()
    dest = dest.resolve()
    if not (src / 'index.html').exists() or not (src / 'main.dart.js').exists():
        raise ValueError('Expected compiled Flutter Web directory with index.html/main.dart.js')
    if dest == src or src in dest.parents:
        raise ValueError('Output must not overwrite the original Cloudflare build')
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(src, dest)
    patched = {}
    for file in sorted(dest.rglob('*')):
        if not file.is_file() or file.suffix.lower() not in SUPPORTED:
            continue
        try:
            before = file.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            continue
        count = before.count(UPSTREAM)
        if not count:
            continue
        # Browser requests are same-origin; the HTTPS gateway handles all APIs.
        after = before.replace(UPSTREAM, '')
        file.write_text(after, encoding='utf-8')
        patched[str(file.relative_to(dest))] = count
    required = {'main.dart.js', 'index.html', 'setup.html', 'finish-registration.html', 'activate-admin.html'}
    if not required.issubset(patched):
        raise RuntimeError(f'Unexpected Web build: missing URL replacements in {sorted(required - patched)}')
    for file in dest.rglob('*'):
        if file.is_file() and file.suffix.lower() in SUPPORTED:
            try: content = file.read_text(encoding='utf-8')
            except UnicodeDecodeError: continue
            if UPSTREAM in content:
                raise RuntimeError(f'Supabase public origin still embedded in {file}')
    # Flutter 3.47's service worker is only an unregister-and-reload script;
    # it contains no asset digests requiring regeneration. Fail safely if changed.
    sw = dest / 'flutter_service_worker.js'
    if sw.exists():
        body = sw.read_text(encoding='utf-8')
        if 'RESOURCES' in body or 'resources = ' in body:
            raise RuntimeError('PWA service worker contains asset hashes; regenerate hashes before deploying')
    return patched


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    results = prepare(args.source, args.output)
    print('Prepared relative-origin Flutter Web mirror:')
    for name, count in results.items():
        print(f'  {name}: {count} URL(s) replaced')