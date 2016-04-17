# bseditor.tests.test_commands.py
from django.core.management import call_command
from django.test import TestCase

from bseditor.models import Version

from wrench.contexts import capture_stdout

# ============================================================================

class CommandTests(TestCase):
    def test_default_version(self):
        with capture_stdout():
            call_command('defaultversion')
            self.assertEqual(1, Version.objects.count())
