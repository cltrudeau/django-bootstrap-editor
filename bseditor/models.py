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

    :param name: human readable name for this instance
    :param compile_filename: fully qualified path to the file to base the
        compilation of the SASS file on.  When building a css file, the custom
        variables are joined together, the contents of this file are put on
        the end and the result is sent to the SASS compiler
    :param variables_filename: fully qualified path to a file to parse to 
        construct the base set of variables that can be customized.  This
        normally points to one of Bootstrap's _variables.scss files.
    """
    name = models.CharField(max_length=50, unique=True)
    compile_filename = models.TextField()
    variables_filename = models.TextField()
    _store = models.TextField()

    @classmethod
    def factory(cls, name, variables_filename, compile_filename):
        variables_filename = os.path.abspath(variables_filename)
        compile_filename = os.path.abspath(compile_filename)

        # validate compile_filename
        src = [
            '$bootstrap-sass-asset-helper:false;',
            '@import "%s";' % compile_filename,
        ]
        sass.compile(string='\n'.join(src))

        # get JSON version of variables file to store using BSV
        bsv = BStrapVars.factory_from_sass_file(variables_filename)

        v = Version.objects.create(name=name, compile_filename=compile_filename,
            variables_filename=variables_filename, _store=bsv.base_to_json())
        return v

    def __str__(self):
        return 'Version(id=%s, name=%s)' % (self.id, self.name)

    def get_vars(self):
        """Returns a BStrapVars object populated with content stored in this 
        instance.
        """
        return BStrapVars.factory(self._store)


@python_2_unicode_compatible
class Sheet(TimeTrackModel):
    """Stores the overridden variables for a specific generated style sheet.

    :param name: human readable name for this customizable style sheet
    :param version: :class:`Version` object this `Sheet` is based upon
    """
    name = models.CharField(max_length=50, unique=True)
    version = models.ForeignKey(Version)
    _store = models.TextField(blank=True)

    @classmethod
    def factory(cls, name, version, custom=None):
        if not custom:
            custom = {}

        bsv = BStrapVars.factory(version._store, custom=custom)
        return Sheet.objects.create(name=name, version=version, 
            _store=bsv.custom_to_json())

    def __str__(self):
        return 'Sheet(id=%s version.id=%s)' % (self.id, self.version.id)

    def get_vars(self, overrides=None):
        """Returns a BStrapVars object populated based on this instance and
        its corresponding :class:`Version`.
        """
        kwargs = {
            'base':self.version._store,
        }
        if self._store:
            kwargs['custom'] = self._store
        if overrides:
            kwargs['overrides'] = overrides

        return  BStrapVars.factory(**kwargs)

    @property
    def filename(self):
        return '%s.css' % slugify(self.name)

    @property
    def full_filename(self):
        return os.path.abspath(os.path.join(settings.BSEDITOR_DEPLOY_DIR, 
            self.filename))

    @property
    def last_deploy(self):
        try:
            last_modified = os.path.getmtime(self.full_filename)
            return When(epoch=last_modified).datetime
        except FileNotFoundError:
            return None

    def compiled_string(self, overrides=None):
        bsv = self.get_vars(overrides)

        src = ['$bootstrap-sass-asset-helper:false;']
        for name, value in bsv.all_value_pairs():
            src.append('$%s:%s;' % (name, value))

        src.append('@import "%s";' % self.version.compile_filename)

        if getattr(settings, 'BSEDITOR_TRACK_LAST_COMPILE', False):
            filename = os.path.abspath(os.path.join(
                settings.BSEDITOR_DEPLOY_DIR, "last_compile.txt"))
            with open(filename, 'w') as f:
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

    :param sheet: :class:`Sheet` object that this `PreviewSheet` is built on
        top of
    """
    sheet = models.ForeignKey(Sheet)
    _store = models.TextField(blank=True)

    @classmethod
    def factory(cls, sheet, overrides):
        bsv = BStrapVars.factory(sheet.version._store, overrides=overrides)
        return PreviewSheet.objects.create(sheet=sheet, 
            _store=bsv.overrides_to_json())

    def __str__(self):
        return 'PreviewSheet(id=%s sheet.id=%s)' % (self.id, self.sheet.id)

    def content(self):
        overrides = None
        if self._store:
            overrides = self._store

        return self.sheet.compiled_string(overrides)
