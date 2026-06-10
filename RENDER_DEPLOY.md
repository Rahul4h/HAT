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

## Cloudinary media uploads

Uploaded product, blog, order, and return images use Cloudinary when
`CLOUDINARY_URL` is set. Existing files that were
previously saved in Render's local `media/` folder must be re-uploaded or
migrated to Cloudinary, because changing storage does not copy old files.

Optional Cloudinary variable:

```env
CLOUDINARY_URL=cloudinary://API_KEY:API_SECRET@CLOUD_NAME
```

## Payment variables

Set payment credentials in Render, not in source code:

```env
STRIPE_PUBLIC_KEY=<your-stripe-public-key>
STRIPE_SECRET_KEY=<your-stripe-secret-key>
SSLCOMMERZ_STORE_ID=<your-sslcommerz-store-id>
SSLCOMMERZ_STORE_PASSWORD=<your-sslcommerz-store-password>
SSLCOMMERZ_API_URL=https://sandbox.sslcommerz.com/gwprocess/v4/api.php
```

## Important free-tier note

Render Free Postgres databases expire after 30 days. Export or upgrade before
expiry if you need to keep the data.
