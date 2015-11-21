# bseditor.models.py
import logging

from django.db import models
from django.utils.encoding import python_2_unicode_compatible

from awl.models import TimeTrackModel

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

    def __str__(self):
        return 'Version(id=%s %s)' % (self.id, self.name)

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
        #sv = SassVariables.factory_from_json(self.variables)
        sv = SassVariables.factory_from_json('{}')
        sv.add_component('gray-base', '#333')

        return sv
