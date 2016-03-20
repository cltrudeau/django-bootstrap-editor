# bseditor.managment.commands.defaultversion.py
#
# Uses the version of Bootstrap shipped in static to create a Version object
# in the database
from __future__ import print_function
import os

from django.core.management.base import BaseCommand

from bseditor.models import Version

versions = (
    ('3.3.5', 'static/bseditor/sass/bootstrap-3.3.5/', 
        'bootstrap/_variables.scss', 'custom.sass', ),
)

class Command(BaseCommand):
    def handle(self, *args, **options):
        global versions
        base_dir = os.path.abspath(os.path.dirname(os.path.dirname(
            os.path.dirname(__file__))))

        for version in versions:
            vars_filename = os.path.join(base_dir, version[1], version[2])
            compile_filename = os.path.join(base_dir, version[1], version[3])
            Version.factory(version[0], vars_filename, compile_filename)
            print('Created Version=%s' % version[0])
