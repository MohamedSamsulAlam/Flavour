import os
from pathlib import Path
import requests
from django.conf import settings
from django.core.management.base import BaseCommand

from apps.accounts.models import User
from apps.restaurants.models import MenuItem, Restaurant


def _cloudinary_env_present():
    if os.environ.get('CLOUDINARY_URL', '').strip():
        return True
    return all(
        os.environ.get(name, '').strip()
        for name in ('CLOUDINARY_CLOUD_NAME', 'CLOUDINARY_API_KEY', 'CLOUDINARY_API_SECRET')
    )


def _find_local_file(db_path):
    if not db_path:
        return None
    normalized = str(db_path).replace('\\', '/').lstrip('/')
    stripped = normalized
    if stripped.startswith('media/'):
        stripped = stripped[len('media/'):]

    candidates = [
        Path(settings.MEDIA_ROOT) / stripped,
        Path(settings.MEDIA_ROOT) / normalized,
        Path(settings.BASE_DIR) / 'media' / stripped,
        Path(settings.BASE_DIR) / normalized,
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


class Command(BaseCommand):
    help = 'Diagnose media storage configuration and sample image URLs'

    def handle(self, *args, **options):
        storage_backend = settings.STORAGES['default']['BACKEND']
        env_present = _cloudinary_env_present()

        self.stdout.write(f'Storage backend: {storage_backend}')
        self.stdout.write(f'MEDIA_URL: {settings.MEDIA_URL}')
        self.stdout.write(f'Cloudinary env vars present: {env_present}')
        self.stdout.write(f'Using MediaCloudinaryStorage: {"MediaCloudinaryStorage" in storage_backend}')

        samples = []
        for label, field in self._iter_image_fields():
            db_path = field.name
            generated_url = field.url if db_path else ''
            is_cloudinary_url = generated_url.startswith('https://res.cloudinary.com/')
            is_local_url = generated_url.startswith('/media/') or (not generated_url.startswith('http'))
            http_status = None
            if generated_url.startswith('http'):
                try:
                    http_status = requests.head(generated_url, timeout=3).status_code
                except requests.RequestException as exc:
                    http_status = f'error:{exc.__class__.__name__}'

            local_exists = bool(db_path and _find_local_file(db_path))
            sample = {
                'label': label,
                'db_path': db_path,
                'generated_url': generated_url,
                'is_cloudinary_url': is_cloudinary_url,
                'is_local_url': is_local_url,
                'http_status': http_status,
                'local_file_exists': local_exists,
            }
            samples.append(sample)

            self.stdout.write(
                f'[{label}] db={db_path!r} url={generated_url} '
                f'cloudinary={is_cloudinary_url} local={is_local_url} '
                f'http={http_status} local_file={local_exists}'
            )

        if not samples:
            self.stdout.write('No image records found in the database.')

        missing_on_cloudinary = sum(
            1 for sample in samples if sample['is_cloudinary_url'] and sample['http_status'] == 404
        )
        fallback_storage = 'FileSystemStorage' in storage_backend

        if fallback_storage:
            self.stdout.write(self.style.WARNING(
                'Cloudinary is NOT active. Falling back to local FileSystemStorage.'
            ))
        elif missing_on_cloudinary:
            self.stdout.write(self.style.WARNING(
                'Cloudinary URLs are configured but some assets return HTTP 404. '
                'Run "python manage.py migrate_media_to_cloudinary" to upload existing files.'
            ))
        elif samples:
            self.stdout.write(self.style.SUCCESS('Sample image URLs look correctly configured and accessible.'))

    def _iter_image_fields(self):
        for restaurant in Restaurant.objects.exclude(logo='').exclude(logo__isnull=True)[:3]:
            if restaurant.logo:
                yield f'restaurant:{restaurant.pk}:logo', restaurant.logo
        for restaurant in Restaurant.objects.exclude(cover_image='').exclude(cover_image__isnull=True)[:3]:
            if restaurant.cover_image:
                yield f'restaurant:{restaurant.pk}:cover', restaurant.cover_image
        for item in MenuItem.objects.exclude(image='').exclude(image__isnull=True)[:5]:
            if item.image:
                yield f'menuitem:{item.pk}', item.image
        for user in User.objects.exclude(avatar='').exclude(avatar__isnull=True)[:2]:
            if user.avatar:
                yield f'user:{user.pk}:avatar', user.avatar
