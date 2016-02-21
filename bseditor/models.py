# bseditor.models.py
import logging, os

from django.conf import settings
from django.core.management import call_command
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.text import slugify

import sass
from awl.absmodels import TimeTrackModel
from wrench.utils import When, dynamic_load

from .conv import BStrapVars

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
    base_file_name = models.CharField(max_length=80)
    store = models.TextField()

    def __str__(self):
        return 'Version(id=%s, name=%s)' % (self.id, self.name)

    def get_vars(self):
        """Returns a BStrapVars object populated with content stored in this 
        instance.
        """
        return BStrapVars.factory(self.store)


@python_2_unicode_compatible
class Sheet(TimeTrackModel):
    """Stores the overridden variables for a specific generated style sheet.
    """
    name = models.CharField(max_length=50, unique=True)
    version = models.ForeignKey(Version)
    store = models.TextField(blank=True)

    def __str__(self):
        return 'Sheet(id=%s version.id=%s)' % (self.id, self.version.id)

    def get_vars(self, overrides=None):
        """Returns a BStrapVars object populated based on this instance and
        its corresponding :class:`Version`.
        """
        kwargs = {
            'base':self.version.store,
        }
        if self.store:
            kwargs['custom'] = self.store
        if overrides:
            kwargs['overrides'] = overrides

        return  BStrapVars.factory(**kwargs)

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
        import_file_name = os.path.abspath(os.path.join(os.path.dirname(
            __file__), 'static/bseditor/sass', self.version.base_file_name))

        src = ['$bootstrap-sass-asset-helper:false;']
        for name, value in self.get_vars().all_value_pairs():
            src.append('$%s:%s;' % (name, value))

        src.append('@import "%s";' % import_file_name)

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
    store = models.TextField(blank=True)

    def __str__(self):
        return 'PreviewSheet(id=%s sheet.id=%s)' % (self.id, self.sheet.id)

    def content(self):
        overrides = None
        if self.store:
            overrides = self.store

        return self.sheet.compiled_string(overrides)
