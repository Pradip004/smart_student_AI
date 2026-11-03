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
