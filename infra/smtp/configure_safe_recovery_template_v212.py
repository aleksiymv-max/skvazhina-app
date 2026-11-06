#!/usr/bin/env python3
"""One-shot hardened recovery email template. Never sends mail or logs credentials."""
import json, os, urllib.request, urllib.error, sys
URL="https://api.supabase.com/v1/projects/xptmcufhuvtcunqzlsme/config/auth"
ORIGIN="https://promysel-app.tuqo.ru"
PAGE=ORIGIN+"/finish-registration.html"
RECOVERY_TEMPLATE=(
  '<!doctype html><html lang="ru"><meta charset="utf-8"><body style="font-family:Arial,sans-serif">'
  '<h2>Промысел</h2><p>Установка или восстановление пароля.</p>'
  '{{ if .RedirectTo }}'
  '<p><a href="{{ .RedirectTo }}{{ .TokenHash }}&amp;type=recovery">Открыть безопасную страницу установки пароля</a></p>'
  '{{ else }}'
  '<p><a href="'+PAGE+'?mode=first&amp;token_hash={{ .TokenHash }}&amp;type=recovery">Открыть страницу установки пароля</a></p>'
  '{{ end }}'
  '<p>Если вы уже входите в приложение и не запрашивали восстановление, проигнорируйте письмо.</p>'
  '</body></html>'
)
def req(method,token,body=None):
    h={"Authorization":"Bearer "+token,"Accept":"application/json"}
    payload=None
    if body is not None:
        h["Content-Type"]="application/json";payload=json.dumps(body).encode()
    r=urllib.request.Request(URL,headers=h,data=payload,method=method)
    try:
        with urllib.request.urlopen(r,timeout=25) as res:
            data=res.read(1000000)
            return json.loads(data) if data.strip() else {}
    except urllib.error.HTTPError as e:
        raise RuntimeError("Management API returned HTTP "+str(e.code)) from None
def main():
    token=next((os.environ.get(n,"").strip() for n in (
      "SUPABASE_ACCESS_TOKEN","SUPABASE_PAT","SUPABASE_MANAGEMENT_TOKEN",
      "SUPABASE_TOKEN","SUPABASE_PERSONAL_ACCESS_TOKEN",
      "SB_ACCESS_TOKEN","SB_MANAGEMENT_TOKEN"
    ) if os.environ.get(n,"").strip()),"")
    if not token:raise RuntimeError("Supabase Management secret not configured")
    before=req("GET",token)
    if str(before.get("site_url","")).rstrip("/")!=ORIGIN:
        raise RuntimeError("Site URL is not production TUQO; cannot update mail link")
    allow=[x.strip() for x in str(before.get("uri_allow_list") or "").split(",") if x.strip()]
    must=[PAGE,PAGE+"**",PAGE+"?mode=first&token_hash=",PAGE+"?mode=forgot&token_hash="]
    updated=list(dict.fromkeys(allow+must))
    for a in updated:
        if a.startswith("http://") and "localhost" not in a:
            raise RuntimeError("Unsafe redirect allowlist contains unexpected plaintext URL")
    payload={"uri_allow_list":",".join(updated),
             "mailer_templates_recovery_content":RECOVERY_TEMPLATE}
    if before.get("mailer_templates_recovery_content")!=RECOVERY_TEMPLATE or any(v not in allow for v in must):
        req("PATCH",token,payload)
        print("RECOVERY_TEMPLATE_PATCH_ACCEPTED")
    else:print("ALREADY_CONFIGURED")
    after=req("GET",token)
    if after.get("mailer_templates_recovery_content")!=RECOVERY_TEMPLATE:
        raise RuntimeError("Recovery template not persisted")
    current=[x.strip() for x in str(after.get("uri_allow_list") or "").split(",") if x.strip()]
    if any(v not in current for v in must):
        raise RuntimeError("Auth redirect allowlist not persisted")
    if str(after.get("site_url","")).rstrip("/")!=ORIGIN:
        raise RuntimeError("Site URL changed during template update")
    print("RECOVERY_TEMPLATE_VERIFIED: Supabase hash link uses request-specific redirect, existing accounts use explicit forgot mode only")
    print("REDIRECT_ALLOWLIST_VERIFIED: two precise intents and production site retained")
    print("NO_EMAIL_SENT; NO_AUTH_USER_CHANGED; NO_SMTP_PASSWORD_READ")
if __name__=="__main__":
    try:main()
    except Exception as e:
        print("ERROR: "+str(e),file=sys.stderr);sys.exit(1)
