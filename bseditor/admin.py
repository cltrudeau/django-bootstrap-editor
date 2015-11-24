import os
from django.contrib import admin
from django.core.urlresolvers import reverse

from awl.admintools import make_admin_obj_mixin
from wrench.utils import When

from .models import Version, Sheet

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


mixin = make_admin_obj_mixin('Sheet')
mixin.add_obj_link('show_version', 'version')

@admin.register(Sheet)
class SheetAmin(admin.ModelAdmin, mixin):
    list_display = ('id', 'name', 'show_version', 'updated', 'show_filedate', 
        'show_actions')

    def show_actions(self, obj):
        actions = []

        url = reverse('bseditor-edit-sheet', args=(obj.id,))
        actions.append('<a href="%s">Edit</a>' % url)

        url = reverse('bseditor-preview-sheet', args=(obj.id,))
        actions.append('<a target="_blank" href="%s">Preview</a>' % url)

        if obj.out_of_date():
            url = reverse('bseditor-deploy-sheet', args=(obj.id,))
            actions.append('<a href="%s">Deploy</a>' % url)

        return ',&nbsp;'.join(actions)

    show_actions.short_description = 'Actions'
    show_actions.allow_tags = True

    def show_filedate(self, obj):
        try:
            last_modified = os.path.getmtime(obj.full_filename)
            return When(epoch=last_modified).datetime
        except FileNotFoundError:
            return '<i>no file</i>'
    show_filedate.short_description = 'File Changed'
    show_filedate.allow_tags = True
