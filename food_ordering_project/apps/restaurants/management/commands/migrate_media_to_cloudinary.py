import os
from pathlib import Path
import cloudinary.uploader
import requests
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.accounts.models import User
from apps.restaurants.models import MenuItem, Restaurant


def _cloudinary_active():
    backend = settings.STORAGES['default']['BACKEND']
    return 'MediaCloudinaryStorage' in backend


def _find_local_file(db_path):
    if not db_path:
        return None

    # Normalize slashes and strip leading 'media/' if already present
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


def _get_public_id(db_path):
    normalized = str(db_path).replace('\\', '/').lstrip('/')
    if not normalized.startswith('media/'):
        normalized = f'media/{normalized}'
    # Remove file extension for Cloudinary public ID
    stem, _ = os.path.splitext(normalized)
    return stem


class Command(BaseCommand):
    help = 'Upload existing local media files to Cloudinary without deleting database records'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be uploaded without making changes',
        )

    def handle(self, *args, **options):
        if not _cloudinary_active():
            raise CommandError(
                'Cloudinary storage is not active. Set CLOUDINARY_CLOUD_NAME, '
                'CLOUDINARY_API_KEY, and CLOUDINARY_API_SECRET (or CLOUDINARY_URL) first.'
            )

        dry_run = options['dry_run']
        uploaded = 0
        skipped = 0
        missing_local = 0

        self.stdout.write(self.style.MIGRATE_HEADING('Migrating media files to Cloudinary...'))

        for label, field in self._iter_image_fields():
            db_path = field.name
            if not db_path:
                continue

            public_id = _get_public_id(db_path)
            from django.core.files.storage import default_storage
            remote_url = default_storage.url(db_path)

            try:
                head = requests.head(remote_url, timeout=3)
                if head.status_code == 200:
                    skipped += 1
                    self.stdout.write(f'SKIP (already on Cloudinary): {label} -> {public_id}')
                    continue
            except requests.RequestException:
                pass

            local_path = _find_local_file(db_path)
            if not local_path:
                missing_local += 1
                self.stdout.write(self.style.WARNING(
                    f'MISSING local file for {label}: db={db_path}'
                ))
                continue

            if dry_run:
                self.stdout.write(f'DRY RUN: Would upload {label} ({local_path}) -> {public_id}')
                uploaded += 1
                continue

            try:
                with local_path.open('rb') as handle:
                    response = cloudinary.uploader.upload(
                        handle,
                        public_id=public_id,
                        overwrite=True,
                        resource_type='image',
                    )

                new_public_id = response.get('public_id', public_id)
                self.stdout.write(self.style.SUCCESS(f'Uploaded {label} -> {new_public_id}'))
                uploaded += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Failed to upload {label}: {e}'))

        self.stdout.write('')
        self.stdout.write(f'Uploaded: {uploaded}')
        self.stdout.write(f'Skipped (already on Cloudinary): {skipped}')
        self.stdout.write(f'Missing local files: {missing_local}')

    def _iter_image_fields(self):
        for restaurant in Restaurant.objects.all():
            if restaurant.logo:
                yield f'restaurant:{restaurant.pk}:logo', restaurant.logo
            if restaurant.cover_image:
                yield f'restaurant:{restaurant.pk}:cover', restaurant.cover_image
        for item in MenuItem.objects.all():
            if item.image:
                yield f'menuitem:{item.pk}', item.image
        for user in User.objects.all():
            if user.avatar:
                yield f'user:{user.pk}:avatar', user.avatar
