# Smart Student AI

Django app for searching and managing student records. The directory, AI search,
imports, and reports require a signed-in account.

## Local development

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

By default, local development uses the ignored `db.sqlite3` file. To use MySQL
or PostgreSQL, set `DATABASE_URL` in the environment. Never commit database
files or credentials.

AI search uses Ollama. Set `OLLAMA_URL` to a reachable Ollama `/api/generate`
endpoint and optionally set `OLLAMA_MODEL` before running searches.

## Render deployment

1. Push this repository to a private GitHub repository and connect it to Render.
2. Create the Render Blueprint from `render.yaml`. Review Render's current
   service and database charges before provisioning; the Blueprint uses
   persistent paid service tiers.
3. Set `OLLAMA_URL` in the Render service environment to your hosted Ollama
   endpoint. Do not commit credentials or tokens.
4. After the first deployment, open the Render Shell and run
   `python manage.py createsuperuser` to create the initial sign-in.
5. Import student data after signing in. The local database is intentionally
   excluded from Git and is not copied to the hosted database.

The Render Blueprint configures PostgreSQL, HTTPS, static files, database
migrations, and a generated Django secret key. `DJANGO_DEBUG` is disabled for
the hosted service.

## Vercel deployment

Vercel detects this Django project from `manage.py` and serves its static files
from the CDN. Import the GitHub repository in Vercel and set these project
environment variables before deploying:

- `DJANGO_SECRET_KEY`: a newly generated, private Django secret.
- `DJANGO_DEBUG`: `false`.
- `DATABASE_URL`: the connection string for a persistent PostgreSQL database.
- `OLLAMA_URL`: a publicly reachable Ollama `/api/generate` endpoint.
- `OLLAMA_MODEL`: a model available at that endpoint, if not `gemma3:4b`.
- `ALLOWED_HOSTS`: add any custom domain not provided by Vercel's deployment
  environment.
- `CSRF_TRUSTED_ORIGINS`: optional for custom domains; Vercel deployment URLs
  and `*.vercel.app` origins are trusted automatically by Django.

SQLite is suitable only for local development; Vercel's function filesystem is
not persistent. Production builds run `python manage.py migrate --noinput`
against the configured database and fail if `DATABASE_URL` is missing. After
deploying, create the initial account with
`python manage.py createsuperuser` from a trusted environment configured to use
the hosted database. Never commit database URLs, secrets, or local environment
files.
