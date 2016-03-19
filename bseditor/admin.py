from django.contrib import admin
from django.core.urlresolvers import reverse

from awl.admintools import make_admin_obj_mixin

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
class SheetAdmin(admin.ModelAdmin, mixin):
    list_display = ('id', 'name', 'show_version', 'updated', 'filename', 
        'show_filedate', 'show_actions')

    def show_actions(self, obj):
        actions = []

        url = reverse('bseditor-edit-sheet', args=(obj.id,))
        actions.append('<a href="%s">Edit</a>' % url)

        url = reverse('bseditor-preview-saved', args=(obj.id,))
        actions.append('<a target="_blank" href="%s">Preview</a>' % url)

        if obj.out_of_date():
            url = reverse('bseditor-deploy-sheet', args=(obj.id,))
            actions.append('<a href="%s">Deploy</a>' % url)

        return ',&nbsp;'.join(actions)

    show_actions.short_description = 'Actions'
    show_actions.allow_tags = True

    def show_filedate(self, obj):
        when = obj.last_deploy
        if not when:
            return '<i>no file</i>'

        return when
    show_filedate.short_description = 'File Changed'
    show_filedate.allow_tags = True
