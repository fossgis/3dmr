import logging
from django.db import connection
from django.db.models.signals import pre_migrate

logger = logging.getLogger(__name__)

def enable_hstore(sender, **kwargs):
    logger.info("Enabling hstore extension...")
    with connection.cursor() as cursor:
        try:
            cursor.execute("CREATE EXTENSION IF NOT EXISTS hstore;")
            logger.info("hstore extension enabled successfully.")
        except Exception as e:
            logger.error("Failed to enable hstore extension.", exc_info=True)
            raise RuntimeError("hstore installation failed.") from e

pre_migrate.connect(enable_hstore)
