from django.contrib import admin
from django.core.urlresolvers import reverse

#from awl.admintools import make_admin_obj_mixin

from .models import Version

# ============================================================================

@admin.register(Version)
class VersionAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'show_actions',)

    def show_actions(self, obj):
        actions = []

        url = reverse('bseditor-show-version-variables', args=(obj.id,))
        actions.append('<a target="_blank" href="%s">Show Variables</a>' % url)

        url = reverse('bseditor-create-sheet', args=(obj.id,))
        actions.append('<a href="%s">Create Sheet</a>' % url)

        return ',&nbsp;'.join(actions)

    show_actions.short_description = 'Actions'
    show_actions.allow_tags = True
