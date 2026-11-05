web_release: v1.92
purpose: verified-only Web build after client request optimization
apk: disabled
production: no direct deploy from build; only promotion after success

request: v1.92 request routing audit and pending owner-change race fix
source_commit: 792ae07454ee4bcb0cd2d870c82ffa18b188398a

release_requested: v1.93 employee deletion changes, Web DEV first

retry_web: v1.93 robust registration service replacement after initial patch mismatch

retry_web: v1.93 admin layout insensitive cleanup button

web_release: v1.94
purpose: area, pad and well CRUD with durable tombstones
source_commit: 9cb4c4e7f88032fe0c572141370149df8eca3ddc
no_apk: true
production: promote only after confirmed DEV tests

request: v1.95 newer-name conflict protection and durable chief-only structure deletion
source_commit: 19502be9f06fc4e0a2596b5a6e1d4d46008f5607
