# bseditor.tests.test_commands.py
import os

from django.core.management import call_command
from django.test import TestCase

from bseditor.models import Version
from bseditor.management.commands.defaultversion import versions

from wrench.contexts import capture_stdout

# ============================================================================

class CommandTests(TestCase):
    def test_default_version(self):
        with capture_stdout():
            call_command('defaultversion')
            self.assertEqual(1, Version.objects.count())

    def test_create_version(self):
        version = versions[0]
        base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        vars_filename = os.path.join(base_dir, version[1], version[2])
        compile_filename = os.path.join(base_dir, version[1], version[3])

        with capture_stdout():
            call_command('createversion', version[0], vars_filename, 
                compile_filename)
            self.assertEqual(1, Version.objects.count())
