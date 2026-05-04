# Render Deploy Notes

## Recommended Render settings

If you deploy manually:

- Build Command: `bash build.sh`
- Start Command: `python manage.py migrate && python manage.py ensure_superuser && gunicorn project.wsgi:application`
- Instance Type: Free
- Database: Render Postgres Free

If you deploy with Blueprint, use `render.yaml`.

## Required environment variables

Set these once in Render:

```env
DEBUG=False
ALLOWED_HOSTS=.onrender.com
CSRF_TRUSTED_ORIGINS=https://*.onrender.com
DATABASE_URL=<Render Postgres internal connection string>
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=your-email@example.com
DJANGO_SUPERUSER_PASSWORD=your-strong-password
```

The deploy command runs migrations and creates/updates the superuser
automatically, so you do not need Render Shell for that.

## Important free-tier note

Render Free Postgres databases expire after 30 days. Export or upgrade before
expiry if you need to keep the data.
