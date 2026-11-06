#!/usr/bin/env python3
"""Read-only check for active Supabase Auth SMTP and hourly email cap.
Never prints keys, email addresses, passwords, or complete config.
"""
import json
import os
import sys
import urllib.request
import urllib.error

def main():
    tok = next((os.environ.get(k,"").strip() for k in
        ["SUPABASE_ACCESS_TOKEN","SUPABASE_PAT","SUPABASE_MANAGEMENT_TOKEN",
         "SUPABASE_TOKEN","SUPABASE_PERSONAL_ACCESS_TOKEN","SB_ACCESS_TOKEN",
         "SB_MANAGEMENT_TOKEN"] if os.environ.get(k,"").strip()),"")
    if not tok:
        print("CHECK_UNAVAILABLE: no Supabase Management API credential")
        return 2
    url="https://api.supabase.com/v1/projects/xptmcufhuvtcunqzlsme/config/auth"
    req=urllib.request.Request(url,headers={"Authorization":"Bearer "+tok,"Accept":"application/json"})
    try:
        with urllib.request.urlopen(req,timeout=25) as response:
            obj=json.load(response)
    except urllib.error.HTTPError as err:
        print("CHECK_UNAVAILABLE: Management API HTTP "+str(err.code))
        return 3
    host=str(obj.get("smtp_host") or "").lower().strip()
    if host=="smtp.gmail.com":
        print("ACTIVE_SMTP_HOST: Gmail")
    elif host:
        print("ACTIVE_SMTP_HOST: other custom SMTP")
    else:
        print("ACTIVE_SMTP_HOST: not configured")
    print("ACTIVE_SMTP_PORT:",str(obj.get("smtp_port") or "unset"))
    cap=obj.get("rate_limit_email_sent")
    print("SUPABASE_AUTH_EMAIL_LIMIT_PER_HOUR:",cap if isinstance(cap,int) else "not returned")
    print("CUSTOM_SMTP_ENABLED:",bool(host))
    print("CHECK_READ_ONLY: no changes, emails, passwords or identities")
    return 0
if __name__=="__main__":raise SystemExit(main())
