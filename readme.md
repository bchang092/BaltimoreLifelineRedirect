# LumaReach

Standalone LumaReach website: service overview, project story, and a private inquiry form. This project is independent of the sibling `Baltimore-Lifeline` application: separate settings, routes, database, assets, and admin. Links to Baltimore Lifeline open its existing website.

## Run locally

From this folder:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
DEBUG=true .venv/bin/python -B manage.py migrate
DEBUG=true .venv/bin/python -B manage.py runserver 127.0.0.1:8001
```

Open http://127.0.0.1:8001/. Baltimore Lifeline can run separately on its usual port 8000.

- Main page: `templates/luma_home.html`
- Styling: `static/luma.css`
- Inquiry handling: `inquiries/views.py`
- Local database: `db.sqlite3` (ignored by Git)

## Inquiries

Submissions are validated, protected by CSRF, a honeypot, and a database-backed rate limit, then saved privately. Create an admin account with `DEBUG=true .venv/bin/python -B manage.py createsuperuser` and review **Service inquiries** at `/admin/`. Admin accounts are separate from Baltimore Lifeline.

Email notifications are addressed to **baltimorelifeline@gmail.com**. To enable sending, export `EMAIL_HOST_USER` and a Gmail app password as `EMAIL_HOST_PASSWORD`. Inquiries remain saved when email fails. No live notifications are sent by the tests. `.env.example` documents configuration; `.env` files are not loaded automatically.

## Tests

```sh
DEBUG=true .venv/bin/python -B manage.py test inquiries --noinput
DEBUG=true .venv/bin/python -B manage.py check
```

For production, set `DEBUG=false`, a unique `SECRET_KEY`, and the deployed hostname in `ALLOWED_HOSTS`; run migrations and `collectstatic`, and serve `config.wsgi:application` using a production WSGI server. The SQLite database requires persistent storage. Hosting and domain setup have not been configured.
