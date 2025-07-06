from django.core.management.base import BaseCommand
from django.db import transaction
from mainapp.models import Model, LatestModel


class Command(BaseCommand):
    help = 'Sync LatestModel with the latest revision of each Model'

    def add_arguments(self, parser):
        parser.add_argument(
            '--model-id',
            type=int,
            help='Sync only a specific model_id',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force sync even if LatestModel already exists',
        )

    def handle(self, *args, **options):
        model_id = options.get('model_id')
        dry_run = options.get('dry_run')
        force = options.get('force')

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))

        if model_id:
            model_ids = [model_id]
            self.stdout.write(f'Syncing model_id: {model_id}')
        else:
            model_ids = Model.objects.values_list('model_id', flat=True).distinct()
            self.stdout.write(f'Found {len(model_ids)} unique model_ids to sync')

        synced_count = 0
        skipped_count = 0
        error_count = 0

        for current_model_id in model_ids:
            try:
                latest_model = Model.objects.filter(
                    model_id=current_model_id
                ).order_by('-revision').first()

                if not latest_model:
                    self.stdout.write(
                        self.style.WARNING(f'No models found for model_id: {current_model_id}')
                    )
                    continue

                latest_model_exists = LatestModel.objects.filter(
                    model_id=current_model_id
                ).exists()

                if latest_model_exists and not force:
                    self.stdout.write(
                        self.style.WARNING(
                            f'LatestModel for model_id {current_model_id} already exists. '
                            f'Use --force to override.'
                        )
                    )
                    skipped_count += 1
                    continue

                if dry_run:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Would sync model_id {current_model_id} '
                            f'(revision {latest_model.revision})'
                        )
                    )
                    synced_count += 1
                    continue

                with transaction.atomic():
                    latest_model_obj, created = LatestModel.objects.update_or_create(
                        model_id=current_model_id,
                        defaults={
                            'author': latest_model.author,
                            'revision': latest_model.revision,
                            'title': latest_model.title,
                            'description': latest_model.description,
                            'rendered_description': latest_model.rendered_description,
                            'upload_date': latest_model.upload_date,
                            'location': latest_model.location,
                            'license': latest_model.license,
                            'tags': latest_model.tags,
                            'rotation': latest_model.rotation,
                            'scale': latest_model.scale,
                            'translation_x': latest_model.translation_x,
                            'translation_y': latest_model.translation_y,
                            'translation_z': latest_model.translation_z,
                            'is_hidden': latest_model.is_hidden,
                        }
                    )

                    latest_model_obj.categories.clear()
                    latest_model_obj.categories.add(*latest_model.categories.all())

                action = 'Created' if created else 'Updated'
                self.stdout.write(
                    self.style.SUCCESS(
                        f'{action} LatestModel for model_id {current_model_id} '
                        f'(revision {latest_model.revision})'
                    )
                )
                synced_count += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'Error syncing model_id {current_model_id}: {str(e)}'
                    )
                )
                error_count += 1

        self.stdout.write(self.style.SUCCESS(f'\nSync completed:'))
        self.stdout.write(f'    Synced: {synced_count}')
        self.stdout.write(f'    Skipped: {skipped_count}')
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f'  Errors: {error_count}'))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\nThis was a dry run. No changes were made.'))