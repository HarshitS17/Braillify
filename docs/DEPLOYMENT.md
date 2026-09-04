# Deployment Guide & Architecture Recommendation

## Current status: Vercel (single project)

- **URL:** https://braillify.vercel.app (frontend + backend on one domain)
- **Bundle:** 304.90 MB (limit 500 MB) — was 541.39 MB before trimming
- `backend/requirements.txt` = runtime-only deps; `backend/requirements-dev.txt` = dev/test tooling
- Storage falls back to `/tmp` on serverless (see `app/core/config.py`); set
  `TACTILE_ED_WORKSPACE_DIR` to override.

### Known limitation of the Vercel deployment

Vercel Functions are **stateless and multi-instance**. This app persists all
state to a local filesystem (`workspace/`). On serverless:

- each concurrent request can be routed to a different instance with its own
  empty `/tmp` (symptom: sporadic `404 Diagram ... not found` when the browser
  issues parallel requests),
- `/tmp` is wiped on scale-to-zero (work disappears after idle periods),
- the filesystem is read-only outside `/tmp`.

The frontend therefore issues its requests **sequentially** (see
`InteractiveEditor.tsx`), which keeps a single active user session on one warm
instance — enough for demos and the E2E suite, but **not durable production
persistence**.

## Recommended production architecture

```
React/Vite  ──►  Vercel  (static hosting + CDN)
                       │  VITE_API_BASE_URL=https://braillify-api.<host>
                       ▼
FastAPI + CV pipeline  ──►  Railway / Render / Fly.io  (long-running container)
                            docker/Dockerfile.backend + persistent volume
```

Why this is the right shape:

1. **The backend is stateful by design** (filesystem JSON store, uploaded page
   images, generated diagrams). A long-running container with a mounted volume
   matches it with zero code changes.
2. **The CV stack (OpenCV, NumPy, PyMuPDF) is ~305 MB of dependencies** — it
   fits Vercel's size limit but pays cold-start latency on every scale-up; a
   container stays warm and starts in milliseconds.
3. **Processing is synchronous and CPU-bound** (1–3 s per diagram); a
   always-on container avoids per-request cold starts entirely.
4. **The frontend gains nothing from serverless** — it is a static Vite build;
   Vercel's CDN is the ideal host for it.

### Deploy steps (Railway example)

Backend:
1. Create a Railway service from the repo, root directory `backend/`, using
   `docker/Dockerfile.backend`.
2. Mount a volume at `/app/workspace` (or set `TACTILE_ED_WORKSPACE_DIR` to the
   volume path).
3. Note the public URL, e.g. `https://braillify-api.up.railway.app`.

Frontend (Vercel):
4. Set `VITE_API_BASE_URL=https://braillify-api.up.railway.app` in the Vercel
   project env vars and redeploy (the API client already reads it — see
   `frontend/src/services/api.ts`).
5. Backend CORS already allows the Vercel domains
   (`app/core/config.py: cors_origins`); add your domain if you use a custom one.

### Local development / self-hosting

Unchanged: `docker compose up` (see `docker-compose.yml`), or
`uvicorn app.main:app` from `backend/` after
`pip install -r requirements.txt -r requirements-dev.txt`.
