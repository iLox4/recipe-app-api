"""
Django command to wait for the database to be avaible
"""
import time

from psycopg import OperationalError as PsycopgOpError

from django.db.utils import OperationalError
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Django command to wait for databse"""

    def add_arguments(self, parser):
        """Add argument for the command"""
        parser.add_argument(
            '--timeout',
            type=int,
            default=30,
            help='Maximum time in seconds to wait for teh database. \
                Default is 30 seconds.'
        )

    def handle(self, *args, **options):
        """Entrypoint for the command"""
        timeout = options['timeout']
        self.stdout.write('Waiting for database...')

        start_time = time.time()
        while True:
            try:
                self.check(databases=['default'])
                break
            except (PsycopgOpError, OperationalError):
                elapsed = time.time() - start_time
                if elapsed > timeout:
                    self.stdout.write(self.style.ERROR(
                        f'Timed out after {timeout} seconds \
                            waiting for the database.'
                    ))
                    raise Exception('Database unavaible after timeout')
                self.stdout.write('Database is unavaible, waiting 1 second...')
                time.sleep(1)

        self.stdout.write(self.style.SUCCESS('Database is avaible!'))
