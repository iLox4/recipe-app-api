"""
Tests custom managment commands
"""

from unittest.mock import patch

from psycopg import OperationalError as PsycopgOpError

from django.core.management import call_command
from django.db.utils import OperationalError
from django.test import SimpleTestCase


@patch('core.management.commands.wait_for_db.Command.check')
class CommandTests(SimpleTestCase):
    """Test commands"""

    def test_wait_for_db_ready(self, patched_check):
        """Test waiting for database if database is ready"""
        patched_check.return_value = True

        call_command('wait_for_db')

        patched_check.assert_called_once_with(databases=['default'])

    # In the command we will use time sleep to wait between db calls
    # -> in test we dont want to wait so we mocked it
    @patch('time.sleep')
    def test_wait_for_db_delay(self, patched_sleep, patched_check):
        """Test waiting for database when getting OperationalError"""
        # If we want to raise an error -> use side_effect
        # -> it means that first two calls would end with PsycopgError,
        # when 3 times OperationalError,
        # and only after it would return True(Db id ready)
        patched_check.side_effect = [PsycopgOpError] * 2 + \
            [OperationalError] * 3 + [True]

        call_command('wait_for_db')

        self.assertEqual(patched_check.call_count, 6)
        self.assertEqual(patched_sleep.call_count, 5)
        patched_check.assert_called_with(databases=['default'])

    def test_wait_for_db_failed(self, patched_check):
        """Must raise an exception if database is unavaible after timeout"""
        patched_check.side_effect = [PsycopgOpError] * 2

        with self.assertRaises(Exception) as context:
            # Call the command with a timeout of 1 second.
            call_command('wait_for_db', timeout=1)

        self.assertEqual(str(context.exception),
                         'Database unavaible after timeout')
