import cloudinary.uploader
import requests
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.accounts.models import User
from apps.restaurants.models import MenuItem, Restaurant


def _cloudinary_active():
    backend = settings.STORAGES['default']['BACKEND']
    return 'MediaCloudinaryStorage' in backend


def _cloudinary_public_id(db_path):
    prefix = settings.MEDIA_URL.strip('/')
    if prefix and not db_path.startswith(f'{prefix}/'):
        return f'{prefix}/{db_path}'
    return db_path


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

        for label, field in self._iter_image_fields():
            db_path = field.name
            if not db_path:
                continue

            public_id = _cloudinary_public_id(db_path)
            from django.core.files.storage import default_storage
            remote_url = default_storage.url(db_path)
            try:
                head = requests.head(remote_url, timeout=10)
                if head.status_code == 200:
                    skipped += 1
                    self.stdout.write(f'SKIP (already on Cloudinary): {label} -> {public_id}')
                    continue
            except requests.RequestException:
                pass

            local_path = Path(settings.MEDIA_ROOT) / db_path
            if not local_path.exists():
                missing_local += 1
                self.stdout.write(self.style.WARNING(
                    f'MISSING local file for {label}: {local_path}. '
                    'Re-upload this image via admin/forms or copy media from your dev machine first.'
                ))
                continue

            if dry_run:
                self.stdout.write(f'DRY RUN upload: {label} {local_path} -> {public_id}')
                uploaded += 1
                continue

            with local_path.open('rb') as handle:
                response = cloudinary.uploader.upload(
                    handle,
                    public_id=public_id,
                    overwrite=True,
                    resource_type='image',
                )

            new_public_id = response.get('public_id', public_id)
            if field.name != new_public_id:
                field.name = new_public_id
                field.instance.save(update_fields=[field.field.name])

            uploaded += 1
            self.stdout.write(self.style.SUCCESS(f'Uploaded {label} -> {new_public_id}'))

        self.stdout.write('')
        self.stdout.write(f'Uploaded: {uploaded}')
        self.stdout.write(f'Skipped (already remote): {skipped}')
        self.stdout.write(f'Missing local files: {missing_local}')

        if missing_local and not dry_run:
            self.stdout.write(self.style.WARNING(
                'Some records still point to files that were not found locally. '
                'Those images must be re-uploaded through the app/admin after deploy.'
            ))

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
