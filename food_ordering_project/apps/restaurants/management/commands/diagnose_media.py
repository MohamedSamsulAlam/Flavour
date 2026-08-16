import json
import os
import time
from pathlib import Path

import requests
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand

from apps.accounts.models import User
from apps.restaurants.models import MenuItem, Restaurant

LOG_PATH = Path(settings.BASE_DIR).parent / 'debug-2ac106.log'
SESSION_ID = '2ac106'


def _debug_log(location, message, data, hypothesis_id, run_id='diagnose'):
    payload = {
        'sessionId': SESSION_ID,
        'runId': run_id,
        'hypothesisId': hypothesis_id,
        'location': location,
        'message': message,
        'data': data,
        'timestamp': int(time.time() * 1000),
    }
    # #region agent log
    with LOG_PATH.open('a', encoding='utf-8') as log_file:
        log_file.write(json.dumps(payload) + '\n')
    # #endregion


def _cloudinary_env_present():
    if os.environ.get('CLOUDINARY_URL', '').strip():
        return True
    return all(
        os.environ.get(name, '').strip()
        for name in ('CLOUDINARY_CLOUD_NAME', 'CLOUDINARY_API_KEY', 'CLOUDINARY_API_SECRET')
    )


class Command(BaseCommand):
    help = 'Diagnose media storage configuration and sample image URLs'

    def handle(self, *args, **options):
        storage_backend = settings.STORAGES['default']['BACKEND']
        env_present = _cloudinary_env_present()
        settings_cloud_name_set = bool(getattr(settings, 'CLOUDINARY_CLOUD_NAME', ''))

        # #region agent log
        _debug_log(
            'diagnose_media.py:handle',
            'Storage configuration snapshot',
            {
                'storage_backend': storage_backend,
                'media_url': settings.MEDIA_URL,
                'cloudinary_env_present': env_present,
                'settings_cloud_name_set': settings_cloud_name_set,
                'using_cloudinary_storage': 'MediaCloudinaryStorage' in storage_backend,
            },
            'A',
        )
        # #endregion

        self.stdout.write(f'Storage backend: {storage_backend}')
        self.stdout.write(f'MEDIA_URL: {settings.MEDIA_URL}')
        self.stdout.write(f'Cloudinary env vars present: {env_present}')
        self.stdout.write(f'Using MediaCloudinaryStorage: {"MediaCloudinaryStorage" in storage_backend}')

        samples = []
        for label, field in self._iter_image_fields():
            db_path = field.name
            generated_url = field.url if db_path else ''
            is_cloudinary_url = generated_url.startswith('https://res.cloudinary.com/')
            is_local_url = generated_url.startswith('/media/') or generated_url.startswith('http') is False
            http_status = None
            if generated_url.startswith('http'):
                try:
                    http_status = requests.head(generated_url, timeout=10).status_code
                except requests.RequestException as exc:
                    http_status = f'error:{exc.__class__.__name__}'

            sample = {
                'label': label,
                'db_path': db_path,
                'generated_url': generated_url,
                'is_cloudinary_url': is_cloudinary_url,
                'is_local_url': is_local_url,
                'http_status': http_status,
                'local_file_exists': bool(db_path and (settings.MEDIA_ROOT / db_path).exists()),
            }
            samples.append(sample)

            # #region agent log
            _debug_log(
                'diagnose_media.py:sample',
                'Generated image URL sample',
                sample,
                'B' if is_local_url else 'C',
            )
            # #endregion

            self.stdout.write(
                f'[{label}] db={db_path!r} url={generated_url} '
                f'cloudinary={is_cloudinary_url} local={is_local_url} '
                f'http={http_status} local_file={sample["local_file_exists"]}'
            )

        if not samples:
            self.stdout.write('No image records found in the database.')

        local_paths = sum(1 for sample in samples if sample['is_local_url'])
        missing_on_cloudinary = sum(
            1 for sample in samples if sample['is_cloudinary_url'] and sample['http_status'] == 404
        )
        fallback_storage = 'FileSystemStorage' in storage_backend

        # #region agent log
        _debug_log(
            'diagnose_media.py:summary',
            'Diagnosis summary',
            {
                'sample_count': len(samples),
                'local_url_count': local_paths,
                'cloudinary_404_count': missing_on_cloudinary,
                'fallback_storage': fallback_storage,
            },
            'D' if fallback_storage else 'E',
        )
        # #endregion

        if fallback_storage:
            self.stdout.write(self.style.WARNING(
                'Cloudinary is NOT active. Render will serve broken /media/ URLs.'
            ))
        elif missing_on_cloudinary:
            self.stdout.write(self.style.WARNING(
                'Cloudinary URLs are generated but some assets return HTTP 404. '
                'Run migrate_media_to_cloudinary to upload existing files.'
            ))
        elif samples:
            self.stdout.write(self.style.SUCCESS('Sample image URLs look correctly configured.'))

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
