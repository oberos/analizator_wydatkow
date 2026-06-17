---
change_id: fix-local-staticfiles
title: Fix local staticfiles
status: implementing
created: 2026-06-17
updated: 2026-06-17
archived_at: null
---

## Notes

when I run my project locally I dont have CSS at all. Below are logs from devserver: 
[17/Jun/2026 12:49:52] "GET /vendor/bootstrap/bootstrap.bundle.min.js HTTP/1.1" 404 3083
[17/Jun/2026 12:49:52] "GET /vendor/bootstrap/bootstrap.min.css HTTP/1.1" 404 3065
[17/Jun/2026 12:49:52] "GET /app/ui.css HTTP/1.1" 404 2993
[17/Jun/2026 12:49:52] "GET /app/ui.js HTTP/1.1" 404 2990
