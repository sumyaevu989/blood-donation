Deployment to Vercel (Docker container)

This project is configured to build and run on Vercel using a Docker container.

Prerequisites
- Vercel account and project created
- Add the following Environment Variables in Vercel (Project → Settings → Environment Variables):
  - `SECRET_KEY` = <your secret>
  - `DEBUG` = False
  - `ALLOWED_HOSTS` = .your-vercel-domain.vercel.app
  - (Optional) `DATABASE_URL` if using an external DB

What we added to the repo
- `vercel.json` — instructs Vercel to build using the Dockerfile
- `Dockerfile` — installs Python dependencies, runs `collectstatic`, and starts Gunicorn
- `requirements.txt` — Python dependencies (Django, Gunicorn, WhiteNoise, ...)
- `backend_system/settings.py` — reads env vars and is configured to use WhiteNoise and `STATIC_ROOT`

How Vercel deploys
1. Vercel builds the Docker image using the provided `Dockerfile`.
2. The image runs `python manage.py collectstatic` during build, then starts Gunicorn.
3. Gunicorn binds to `$PORT` provided by Vercel and serves the Django app.

Local testing
- You can test the Docker image locally:
```bash
# build
docker build -t blood-donation:local .
# run (map port 8000)
docker run -e SECRET_KEY=dev-secret -e DEBUG=True -p 8000:8000 blood-donation:local
# then open http://localhost:8000
```

Notes
- We use `whitenoise` for static file serving inside the container. `collectstatic` writes files to `staticfiles/` (configured via `STATIC_ROOT`).
- Don't commit your `.env` file. Use Vercel dashboard or CLI to set environment variables.

Troubleshooting
- If the build fails because `collectstatic` raises errors related to missing static references, try running `python manage.py collectstatic --noinput` locally and fix missing assets.
- Check Vercel build logs for Python/Gunicorn errors; they usually indicate missing env vars or dependency issues.
