---
project: "Analizator Wydatkow"
researched_at: 2026-05-28
recommended_platform: Render
runner_up: Railway
context_type: mvp
tech_stack:
  language: python
  framework: django
  runtime: gunicorn
  database: postgresql
---

## Recommendation

**Deploy on Render.**

Render scores highest across all five agent-friendly criteria for a Django MVP: full CLI tooling, GA-level MCP server with 21 agent skills, `llms.txt` documentation, stable deploy API, and managed Postgres. The tech-stack.md already targets Render as the deployment platform, and the interview confirmed no persistent connections are needed (avoiding serverless limitations). Cost sensitivity is addressed by the free tier, with a clear upgrade path to $14-21/mo when the 30-day Postgres trial expires.

## Platform Comparison

| Platform | CLI-first | Managed/Serverless | Agent-readable docs | Stable deploy API | MCP Integration | Total |
|----------|-----------|-------------------|---------------------|-------------------|-----------------|-------|
| **Render** | ✅ Pass | ✅ Pass | ✅ Pass (llms.txt) | ✅ Pass | ✅ Pass (GA MCP + 21 skills) | **5/5** |
| **Railway** | ✅ Pass | ✅ Pass | ✅ Pass (llms.txt) | ⚠️ Partial (no CLI rollback) | ✅ Pass (GA MCP) | **4.5/5** |
| **Fly.io** | ✅ Pass | ✅ Pass | ⚠️ Partial (no llms.txt) | ⚠️ Partial (manual rollback) | ⚠️ Partial (2 tools only) | **3.5/5** |
| **Vercel** | ✅ Pass | ✅ Pass | ✅ Pass (llms.txt) | ✅ Pass | ✅ Pass (GA MCP) | **5/5** |

**Dropped from consideration:**
- **Netlify** — No Python runtime; serverless functions support only TS/JS/Go
- **Cloudflare Workers** — Python via Pyodide (beta); Django/WSGI not supported

### Shortlisted Platforms

#### 1. Render (Recommended)

Render provides first-class Django support with native Python runtime (3.7–3.14), automatic Gunicorn detection, and an official Django deployment guide. The CLI (`render`) supports deploy, log streaming, and service management. Rollback is available via dashboard or API. The MCP server (`render-oss/render-mcp-server`) exposes 15+ tools including `list_services`, `create_web_service`, `list_logs`, `get_metrics`, and `query_render_postgres`. Additionally, 21 agent skills are available for Claude Code, Cursor, and Codex via `render skills install`.

Key strengths:
- Native Django scanner with Gunicorn/Uvicorn auto-configuration
- Free tier includes web services (750 instance-hours) and Postgres (1GB, 30-day trial)
- Full WebSocket support via Django Channels
- Agent-readable docs at `docs.render.com/llms.txt`

#### 2. Railway

Railway offers excellent DX with instant deploys via `railway up`, co-located Postgres/Redis, and a built-in MCP server (`railway mcp`). Python 3.8–3.13 is supported via Nixpacks with automatic Django detection. The $5/mo minimum on Hobby tier is competitive, and database instances don't expire like Render's free tier.

Gap vs Render: No CLI rollback command — rollbacks require dashboard UI. The MCP server is bundled in the CLI rather than standalone, which slightly complicates agent configuration.

#### 3. Vercel

Vercel supports Django as a "full-stack framework" with automatic `manage.py` detection. The MCP server is mature, and the Hobby free tier is generous (1M invocations/month). Documentation is excellent with `llms.txt` available.

Gap vs Render: Serverless-only execution model means no WebSockets, no persistent processes, and Django runs with more friction (cold starts, no SQLite persistence, session state challenges). For a simple expense tracker without real-time features this works, but it's a tighter fit than container-based PaaS.

## Anti-Bias Cross-Check: Render

### Devil's Advocate — Weaknesses

1. **Free tier spin-down (15 min)** — First request after idle incurs ~1 min cold start. For a personal expense tracker used sporadically, this means noticeable delays on every session start.

2. **Free Postgres expires in 30 days** — If you forget to migrate to paid DB, your transaction data is deleted. This is a data-loss footgun for MVP learners.

3. **Rollback disables auto-deploy** — Dashboard rollback turns off git-triggered deploys; API rollback doesn't. Inconsistent behavior could confuse agent workflows.

4. **No CLI rollback command** — Rollback requires API call or dashboard click; agent must parse API response or use MCP server's tool.

5. **Render Workflows still in beta** — If you need task orchestration later, the beta status means API changes without warning.

### Pre-Mortem — How This Could Fail

Six months after deploying Analizator Wydatkow to Render, the decision turned out badly. The free Postgres instance expired on day 31 — the reminder email went to spam, and all user transaction data was lost. Rebuilding from CSV re-imports took a weekend.

The free tier spin-down caused constant complaints: every morning the first CSV upload timed out because the Django app was cold-starting while the request waited. The user assumed the app was broken and filed multiple "bug reports" against themselves.

When attempting the first real deployment fix, the dashboard rollback disabled auto-deploy without warning. The next git push didn't trigger a build. Three hours of debugging later, the setting was found buried in the service config.

The MCP server worked great for log tailing and metrics, but when the agent tried to automate a rollback, it discovered the rollback tool wasn't in the MCP schema — it had to fall back to raw API calls, which required learning Render's API token scoping (different from the CLI auth).

The final straw: Render's build cache expired after 7 days of inactivity, and a routine dependency update triggered a 12-minute rebuild instead of the expected 2-minute incremental build.

### Unknown Unknowns

1. **Build cache expiration** — Render purges build cache after ~7 days of no deploys. Sporadic hobby projects see full rebuilds regularly.

2. **Region lock** — Free tier is Oregon-only. Polish users experience ~150ms latency per request. Paid tier adds Frankfurt but costs $7+/mo.

3. **No SSH on free tier** — Can't run `manage.py shell` or one-off commands without upgrading or using Render's "Shell" feature (which requires a running service).

4. **Gunicorn worker count** — Render's free tier (512MB) limits you to 1-2 Gunicorn workers. Concurrent CSV uploads may queue.

5. **Static file serving** — Unlike Railway, Render doesn't auto-configure WhiteNoise. You must add it manually or static files 404 in production.

## Operational Story

How Render operates day to day for this Django project:

- **Preview deploys**: Every push to a branch creates a preview URL at `<service>-<branch>.onrender.com`. Preview environments are public by default; add Render Access (paid) to protect them. Fork PRs from external contributors don't get preview builds unless explicitly enabled.

- **Secrets**: Environment variables live in the Render dashboard under Service → Environment. Group-level env vars can be shared across services. Secrets are encrypted at rest but visible to anyone with dashboard access. Rotation: update the value in dashboard → redeploy. No automatic rotation.

- **Rollback**: Dashboard → Deployments → click three-dot menu on any previous deploy → "Rollback". This disables auto-deploy (must re-enable manually). Via API: `POST /v1/services/{serviceId}/deploys/{deployId}/rollback`. Typical time-to-revert: 30-60 seconds. **Caution**: Database migrations don't roll back automatically — if a deploy included `migrate`, the schema change persists.

- **Approval**: Human-required actions: publish to production (first deploy), rotate primary database credentials, delete a database, change billing tier. Agent-safe actions: deploy from existing commit, tail logs, read metrics, restart service.

- **Logs**: CLI: `render logs --service <service-id> --tail`. MCP: `list_logs` tool with service filter. Dashboard: real-time streaming in the Logs tab. Logs retained for 7 days on free tier, 30 days on paid.

## Risk Register

| Risk | Source | Likelihood | Impact | Mitigation |
|------|--------|------------|--------|------------|
| Free Postgres expires, data lost | Pre-mortem | High | High | Set calendar reminder for day 25; upgrade to $7/mo Basic before expiry |
| Cold start delays annoy user | Devil's advocate | High | Low | Accept for MVP; upgrade to Starter ($7/mo) if unacceptable |
| Rollback disables auto-deploy | Devil's advocate | Medium | Medium | After rollback, manually re-enable auto-deploy in dashboard |
| Build cache expires, slow rebuilds | Unknown unknowns | Medium | Low | Deploy at least weekly to keep cache warm; or accept occasional slow builds |
| Oregon region adds 150ms latency | Unknown unknowns | High | Low | Accept for MVP; upgrade to Frankfurt ($7/mo) if scaling to production |
| WhiteNoise not auto-configured | Unknown unknowns | High | Medium | Add `whitenoise` to requirements.txt and configure in settings.py before first deploy |
| No SSH for one-off commands | Unknown unknowns | Medium | Low | Use Render Shell in dashboard or create a one-off job for migrations |
| MCP lacks rollback tool | Pre-mortem | Low | Medium | Use dashboard or API directly for rollbacks; don't rely on MCP for this operation |

## Getting Started

1. **Install the Render CLI**
   ```bash
   # macOS/Linux
   curl -fsSL https://raw.githubusercontent.com/render-oss/cli/main/bin/install.sh | sh
   
   # Windows (PowerShell)
   irm https://raw.githubusercontent.com/render-oss/cli/main/bin/install.ps1 | iex
   ```

2. **Add WhiteNoise for static files**
   ```bash
   pdm add whitenoise
   ```
   Then in `settings.py`:
   ```python
   MIDDLEWARE = [
       'django.middleware.security.SecurityMiddleware',
       'whitenoise.middleware.WhiteNoiseMiddleware',  # Add after SecurityMiddleware
       # ... rest of middleware
   ]
   STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
   ```

3. **Create `render.yaml` Blueprint**
   ```yaml
   services:
     - type: web
       name: analizator-wydatkow
       runtime: python
       buildCommand: |
         pip install -r requirements.txt
         python manage.py collectstatic --no-input
         python manage.py migrate
       startCommand: gunicorn analizator_wydatkow.wsgi:application
       envVars:
         - key: DJANGO_SECRET_KEY
           generateValue: true
         - key: ALLOWED_HOSTS
           value: .onrender.com
   
   databases:
     - name: analizator-db
       plan: free  # Expires in 30 days — upgrade to basic ($7/mo) before expiry
   ```

4. **Connect to Render**
   - Go to [dashboard.render.com](https://dashboard.render.com) → New → Blueprint
   - Connect your GitHub repo
   - Render auto-detects `render.yaml` and provisions services

5. **Set the DATABASE_URL**
   - After database creation, copy the Internal Database URL from the Render dashboard
   - Add it as `DATABASE_URL` environment variable to your web service
   - Configure Django to parse it with `dj-database-url`:
     ```bash
     pdm add dj-database-url
     ```
     ```python
     import dj_database_url
     DATABASES = {'default': dj_database_url.config(conn_max_age=600)}
     ```

## Out of Scope

The following were not evaluated in this research:
- Docker image configuration (Render uses native Python runtime)
- CI/CD pipeline setup (GitHub Actions auto-deploy covered in tech-stack.md)
- Production-scale architecture (multi-region, HA, DR)
- Cost optimization beyond MVP tier
