# bseditor.managment.commands.createversion.py
#
# Creates a Version object from the given parameters
from __future__ import print_function
import os

from django.core.management.base import BaseCommand

from bseditor.models import Version

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('name', help=('Human readable name for the '
            'Version object being created; suggestion: the Bootstrap '
            'version number'))
        parser.add_argument('variables_file', help=('Path to the Bootstrap '
            '"_variables.scss" file'))
        parser.add_argument('custom_file', help=('Path to your "custom.sass" '
            'file'))

    def handle(self, *args, **options):
        variables = os.path.abspath(options['variables_file'])
        custom = os.path.abspath(options['custom_file'])

        version = Version.factory(options['name'], variables, custom)
        print('Created %s' % version)
