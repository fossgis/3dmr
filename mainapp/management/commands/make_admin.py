import logging
from social_django.models import UserSocialAuth
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Make a user admin by username or social auth UID'
    
    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument(
            '--username',
            type=str,
            help='Username of the user to make admin'
        )
        group.add_argument(
            '--uid',
            type=str,
            help='UserSocialAuth UID of the user to make admin'
        )
        parser.add_argument(
            '--dismiss',
            action='store_true',
            help='Dismiss the user from being admin. Use with --username or --uid'
        )
    
    def handle(self, *args, **options):
        username = options.get('username')
        uid = options.get('uid')
        dismiss = options.get('dismiss', False)

        try:
            with transaction.atomic():
                user = None

                if username:
                    try:
                        user = User.objects.get(username=username)
                        logger.info(f"Found user by username: {user.username}")
                    except User.DoesNotExist:
                        error_msg = f"User with username '{username}' does not exist"
                        logger.error(error_msg)
                        raise CommandError(error_msg)

                elif uid:
                    try:
                        social_auth = UserSocialAuth.objects.get(uid=uid)
                        user = social_auth.user
                        logger.info(f"Found user by OSM UID: {user.username}")
                    except UserSocialAuth.DoesNotExist:
                        error_msg = f"UserSocialAuth object with UID '{uid}' does not exist"
                        logger.error(error_msg)
                        raise CommandError(error_msg)
                    except UserSocialAuth.MultipleObjectsReturned:
                        error_msg = (
                            f"Multiple UserSocialAuth records found for UID '{uid}'. "
                            "Consider adding provider filtering if needed"
                        )
                        logger.error(error_msg)
                        raise CommandError(error_msg)
 
                if not user:
                    error_msg = "No user found"
                    logger.error(error_msg)
                    raise CommandError(error_msg)

                updated_fields = []

                if dismiss:
                    if user.profile.is_admin:
                        user.profile.is_admin = False
                        updated_fields.append('is_admin')
                else:
                    if not user.profile.is_admin:
                        user.profile.is_admin = True
                        updated_fields.append('is_admin')
                
                if updated_fields:
                    user.profile.save(update_fields=updated_fields)
                    action = "dismissed from admin" if dismiss else "made admin"
                    logger.info(
                        f"Successfully {action} for user '{user.username}'. "
                        f"Updated fields: {', '.join(updated_fields)}"
                    )
                else:
                    status = "not an admin" if dismiss else "already an admin"
                    logger.info(f"User '{user.username}' is {status}")
                        
        except CommandError:
            raise
        except Exception as e:
            error_msg = f"Error processing user admin status: {str(e)}"
            logger.exception(error_msg)
            raise CommandError(error_msg)
