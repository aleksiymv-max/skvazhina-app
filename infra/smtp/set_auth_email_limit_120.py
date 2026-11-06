#!/usr/bin/env python3
"""One-shot adjust Supabase Auth email volume for verified Gmail SMTP.
Never prints or changes credentials, sender address, templates or user data.
Does not send any emails. Exits nonzero if custom Gmail SMTP is not configured.
"""
import json,os,sys,urllib.error,urllib.request

URL="https://api.supabase.com/v1/projects/xptmcufhuvtcunqzlsme/config/auth"
TARGET=120

def request(method,token,payload=None):
    headers={"Authorization":"Bearer "+token,"Accept":"application/json"}
    if payload is not None:
        headers["Content-Type"]="application/json"
    data=json.dumps(payload).encode() if payload is not None else None
    req=urllib.request.Request(URL,data=data,headers=headers,method=method)
    try:
        with urllib.request.urlopen(req,timeout=25) as res:
            raw=res.read(150000)
            return json.loads(raw) if raw.strip() else {}
    except urllib.error.HTTPError as e:
        raise RuntimeError("Supabase Management API HTTP "+str(e.code)) from None

def main():
    token=next((os.environ.get(n,"").strip() for n in (
        "SUPABASE_ACCESS_TOKEN","SUPABASE_PAT","SUPABASE_MANAGEMENT_TOKEN",
        "SUPABASE_TOKEN","SUPABASE_PERSONAL_ACCESS_TOKEN",
        "SB_ACCESS_TOKEN","SB_MANAGEMENT_TOKEN") if os.environ.get(n,"").strip()),"")
    if not token:raise RuntimeError("Missing Management API credential")
    before=request("GET",token)
    if str(before.get("smtp_host","")).strip().lower()!="smtp.gmail.com":
        raise RuntimeError("Refusing: active SMTP is not Gmail")
    if not before.get("smtp_user"):
        raise RuntimeError("Refusing: Gmail SMTP user not configured")
    old=before.get("rate_limit_email_sent")
    if not isinstance(old,int) or old<=0:raise RuntimeError("Rate limit config not numeric")
    print("CUSTOM_SMTP_GMAIL: verified")
    print("AUTH_EMAIL_LIMIT_BEFORE_PER_HOUR:",old)
    if old!=TARGET:
        request("PATCH",token,{"rate_limit_email_sent":TARGET})
        print("RATE_LIMIT_PATCH_ACCEPTED")
    else:
        print("NO_CHANGE_NEEDED")
    after=request("GET",token)
    if after.get("rate_limit_email_sent")!=TARGET:
        raise RuntimeError("Verification failed: Auth limit differs from requested 120/hour")
    if str(after.get("smtp_host","")).strip().lower()!="smtp.gmail.com":
        raise RuntimeError("Verification failed: SMTP host has changed")
    print("AUTH_EMAIL_LIMIT_VERIFIED_PER_HOUR:",TARGET)
    print("APPLICATION_INTERVAL: 30 seconds per message")
    print("GOOGLE_SMTP_QUOTAS: independent; send throttling or daily caps may still apply")
    print("NO_EMAILS_SENT_OR_USERS_CHANGED")
if __name__=="__main__":
    try:main()
    except Exception as err:
        print("ERROR: "+str(err),file=sys.stderr)
        sys.exit(1)
