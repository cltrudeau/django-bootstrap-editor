# bseditor.models.py
import logging, os, json, datetime
from collections import OrderedDict

from django.conf import settings
from django.core.management import call_command
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.text import slugify

import sass
from awl.models import TimeTrackModel
from wrench.utils import When, dynamic_load

from .conv import SassVariables

logger = logging.getLogger(__name__)

# ============================================================================
# Models
# ============================================================================

@python_2_unicode_compatible
class Version(TimeTrackModel):
    """Instances define the configuration information for a version of
    BootStrap that the compiles CSS will be based upon.   Use the 
    ``./manage.py defaultversion`` command to instantiate the built-in
    version.
    """
    name = models.CharField(max_length=50, unique=True)
    variables = models.TextField()
    basefile = models.CharField(max_length=80)

    def __str__(self):
        return 'Version(id=%s, name=%s)' % (self.id, self.name)

    @property
    def sass_variables(self):
        """Returns the contents of the ``variables`` field as a SassVersion
        object.
        """
        return SassVariables.factory_from_json(self.variables)


@python_2_unicode_compatible
class Sheet(TimeTrackModel):
    """Stores the overridden variables for a specific generated style sheet.
    """
    name = models.CharField(max_length=50, unique=True)
    version = models.ForeignKey(Version)
    variables = models.TextField(blank=True)

    def __str__(self):
        return 'Sheet(id=%s version.id=%s)' % (self.id, self.version.id)

    @property
    def sass_variables(self):
        """Returns the contents of the ``variables`` field as a SassVersion
        object.
        """
        if self.variables:
            overrides = json.loads(self.variables, 
                object_pairs_hook=OrderedDict)
        else:
            overrides = {}

        sv = SassVariables.factory_from_dict({}, overrides)
        return sv

    @property
    def filename(self):
        return '%s.css' % slugify(self.name)

    @property
    def preview_filename(self):
        return '%s.preview.css' % slugify(self.name)

    @property
    def full_filename(self):
        return os.path.abspath(os.path.join(settings.BSEDITOR_DEPLOY_DIR, 
            self.filename))

    def out_of_date(self):
        try:
            last_modified = os.path.getmtime(self.full_filename)
        except FileNotFoundError:
            return True

        last_updated = When(datetime=self.updated).epoch
        return last_modified < last_updated

    def compiled_string(self, overrides=None):
        base = json.loads(self.version.variables, object_pairs_hook=OrderedDict)
        variables = {}
        if self.variables:
            variables = json.loads(self.variables, 
                object_pairs_hook=OrderedDict)

        if overrides:
            variables.update(overrides)

        all_variables = SassVariables.factory_from_dict(base, variables)
        import_file = os.path.abspath(os.path.join(os.path.dirname(__file__),
            'static/bseditor/sass', self.version.basefile))

        src = ['$bootstrap-sass-asset-helper:false;']
        for name, component in all_variables.all_components.items():
            src.append('$%s:%s;' % (name, component.value))

        src.append('@import "%s";' % import_file)

        if getattr(settings, 'BSEDITOR_TRACK_LAST_COMPILE', False):
            with open('last_compile.txt', 'w') as f:
                f.write('\n'.join(src))

        return sass.compile(string='\n'.join(src))


    def deploy(self):
        result = self.compiled_string()

        with open(self.full_filename, 'w') as f:
            f.write(result)

        if getattr(settings, 'BSEDITOR_COLLECT_ON_DEPLOY', False):
            # handle static collection on deployment
            hook = getattr(settings, 'BSEDITOR_COLLECT_HOOK', '')
            if hook:
                # use the defined collection hook instead of collectstatic
                fn = dynamic_load(hook)
                fn(self)
            else:
                # use default collectstatic during deploy
                call_command('collectstatic', '--noinput')


@python_2_unicode_compatible
class PreviewSheet(TimeTrackModel):
    """Stores values for a live-edit sheet that have been changed but not
    saved so that they can be previewed.
    """
    sheet = models.ForeignKey(Sheet)
    variables = models.TextField(blank=True)

    def __str__(self):
        return 'PreviewSheet(id=%s sheet.id=%s)' % (self.id, self.sheet.id)

    def content(self):
        if self.variables:
            variables = json.loads(self.variables, 
                object_pairs_hook=OrderedDict)
        else:
            variables = {}

        return self.sheet.compiled_string(variables)
