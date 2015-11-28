from django.conf.urls import patterns, url

urlpatterns = patterns('bseditor.views',
    # editor patterns
    url(r'edit_sheet/(\d+)/$', 'edit_sheet', name='bseditor-edit-sheet'),
    url(r'ajax_colour_value/$', 'ajax_colour_value',
        name='bseditor-ajax-colour-value'),
    url(r'ajax_save_sheet/(\d+)/$', 'ajax_save_sheet',
        name='bseditor-ajax-save-sheet'),

    # admin patterns
    url(r'show_version_variables/(\d+)/$', 'show_version_variables', 
        name='bseditor-show-version-variables'),
    url(r'create_sheet/(\d+)/$', 'create_sheet', name='bseditor-create-sheet'),
    url(r'deploy_sheet/(\d+)/$', 'deploy_sheet', name='bseditor-deploy-sheet'),

    # preview patterns
    url(r'preview_css/(\d+)/$', 'preview_css', name='bseditor-preview-css'),
    url(r'preview_sheet/(\d+)/$', 'preview_sheet', 
        name='bseditor-preview-sheet'),
    url(r'preview_css/(\d+)/$', 'preview_css', ),
    url(r'show_saved_sheet_preview/(\d+)/$', 'show_saved_sheet_preview', 
        name='bseditor-preview-saved'),
    url(r'ajax_save_preview/(\d+)/$', 'ajax_save_preview',
        name='bseditor-ajax-save-preview'),
)
