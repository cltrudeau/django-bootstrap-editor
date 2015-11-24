# bseditor.managment.commands.defaultversion.py
#
# Uses the version of Bootstrap shipped in static to create a Version object
# in the database
from __future__ import print_function
import os

from django.core.management.base import BaseCommand

from bseditor.conv import SassVariables
from bseditor.models import Version

versions = (
    ('3.3.5', 'bseditor/sass/bootstrap-3.3.5/bootstrap/_variables.scss',
         'bootstrap-3.3.5/custom.sass', ),
)

class Command(BaseCommand):
    def handle(self, *args, **options):
        global versions

        for version in versions:
            filename = os.path.abspath(os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                'static', version[1]))

            sass_values = SassVariables.factory_from_sass_file(filename)
            Version.objects.create(name=version[0], basefile=version[2],
                variables=sass_values.to_json())
            print('Created Version=%s' % version[0])
