from django.conf.urls import patterns, url

urlpatterns = patterns('bseditor.views',
    url(r'show_version_variables/(\d+)/$', 'show_version_variables', 
        name='bseditor-show-version-variables'),
    url(r'create_sheet/(\d+)/$', 'create_sheet', name='bseditor-create-sheet'),
    url(r'edit_sheet/(\d+)/$', 'edit_sheet', name='bseditor-edit-sheet'),
    url(r'ajax_colour_value/$', 'ajax_colour_value',
        name='bseditor-ajax-colour-value'),
)
