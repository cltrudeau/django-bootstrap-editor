import json, logging, sass
from collections import OrderedDict

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db.utils import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt

from awl.decorators import post_required
from awl.utils import render_page

from .conv import BStrapVars
from .models import Sheet, Version, PreviewSheet

logger = logging.getLogger(__name__)

# ============================================================================
# Editor Methods
# ============================================================================

@staff_member_required
def edit_sheet(request, sheet_id):
    sheet = get_object_or_404(Sheet, id=sheet_id)

    data = {
        'sheet':sheet,
        'bstrap_vars':sheet.get_vars(),
        'cancel_url':reverse('admin:bseditor_sheet_changelist'),
        'ajax_colour_value_url':reverse('bseditor-ajax-colour-value'),
        'ajax_save_sheet':reverse('bseditor-ajax-save-sheet', args=(sheet.id,)),
        'ajax_save_preview':reverse('bseditor-ajax-save-preview', 
            args=(sheet.id,)),
    }

    return render_page(request, 'bseditor/edit_sheet.html', data)


@staff_member_required
@csrf_exempt
@post_required(['payload'])
def ajax_save_sheet(request, sheet_id):
    sheet = get_object_or_404(Sheet, id=sheet_id)

    payload = json.loads(request.POST['payload'])

    try:
        sheet.name = payload['name']
        sheet.store = json.dumps(payload['custom'])
        sheet.save()
        sheet.deploy()
        messages.success(request, 'Saved & deployed %s' % sheet.filename)
    except Exception as e:
        logger.exception('Error saving sheet!')
        messages.error(request, 'Error: %s' % str(e))

    return JsonResponse({})


@staff_member_required
@csrf_exempt
@post_required(['payload'])
def ajax_colour_value(request):
    """AJAX method for compiling a CSS colour value within the Bootstrap
    context.  Expects "colour" key in POST dictionary with a string to convert
    into a valid CSS colour.  

    Returns a JSON dictionary with a key "success" that is guaranteed to be
    there.  If the colour value is convertible then another key "colour" will
    contain the result.
    """
    payload = json.loads(request.POST['payload'])
    sass_variable = payload['sass_variable']
    version = get_object_or_404(Version, id=payload['version'])
    content = json.loads(version.store, object_pairs_hook=OrderedDict)
    data = {
        'success':False,
        'colours':{},
    }

    try:
        bsv = BStrapVars.factory(content, overrides=payload['overrides'])
        data['colours'][sass_variable] = bsv.colour_values[sass_variable]
        
        # update any other colours dependent on this variable
        for name in bsv.dependencies(sass_variable):
            try:
                data['colours'][name] = bsv.colour_values[name]
            except KeyError:
                # variable is used in a non-colour, just ignore it
                pass

        data['success'] = True 
    except (sass.CompileError, KeyError):
        # compilation errors, key errors, all should result in the default
        # "success:False" in response
        pass

    return JsonResponse(data)

# ============================================================================
# Admin Methods
# ============================================================================

@staff_member_required
def show_version_variables(request, version_id):
    version = get_object_or_404(Version, id=version_id)

    # use HttpResponse rather than JsonResponse as we don't want to perform
    # the json.dumps() call, BStrapVars must do conversion as it has a
    # specialized encoder
    return HttpResponse(content=version.get_vars().base_to_json(), 
        content_type='application/json')


@staff_member_required
def deploy_sheet(request, sheet_id):
    sheet = get_object_or_404(Sheet, id=sheet_id)

    try:
        sheet.deploy()
        messages.success(request, 'Deployed %s' % sheet.filename)
    except Exception as e:
        logger.exception('Error in deploy!')
        messages.error(request, 'Error deploying: %s' % str(e))

    url = reverse('admin:bseditor_sheet_changelist')
    return HttpResponseRedirect(url)


@staff_member_required
def create_sheet(request, version_id):
    version = get_object_or_404(Version, id=version_id)

    count = 0
    while(True):
        try:
            name = 'new sheet'
            if count:
                name += ' %s' % count

            sheet = Sheet.objects.create(name=name, version=version)
            break
        except IntegrityError: 
            sheet = Sheet.objects.filter(
                name__startswith='new sheet').order_by('created').last()
            try:
                count = int(sheet.name[9:]) + 1
            except ValueError:
                count += 1

    url = reverse('bseditor-edit-sheet', args=(sheet.id,))
    return HttpResponseRedirect(url)

# ============================================================================
# Preview Handling
# ============================================================================

def preview_css(request, preview_sheet_id):
    """Returns a CSS based on the compiled SASS content of the given
    :class:`PreviewSheet` object

    @param preview_sheet_id: ID of :class:`PreviewSheet` object
    """
    preview = get_object_or_404(PreviewSheet, id=preview_sheet_id)

    return HttpResponse(preview.content(), content_type='text/css')


def preview_sheet(request, preview_sheet_id):
    """Displays a sample Bootstrap page using the variables stored in the
    given :class:`PreviewSheet`

    @param preview_sheet_id: ID of :class:`PreviewSheet` object
    """
    preview = get_object_or_404(PreviewSheet, id=preview_sheet_id)
    data = {
        'preview':preview,
        'preview_css_url':reverse('bseditor-preview-css', args=(preview.id,))
    }

    return render_page(request, 'bseditor/preview_sheet.html', data)


@staff_member_required
def show_saved_sheet_preview(request, sheet_id):
    """Given a :class:`Sheet` object, reset any associated 
    :class:`PreviewSheet` and redirect to the :func:`preview_sheet` view

    @param sheet_id: ID of :class`Sheet` object
    """
    sheet = get_object_or_404(Sheet, id=sheet_id)
    try:
        preview = PreviewSheet.objects.get(sheet=sheet)
        preview.store = ''
        preview.save()
    except PreviewSheet.DoesNotExist:
        preview = PreviewSheet.objects.create(sheet=sheet)

    url = reverse('bseditor-preview-sheet', args=(preview.id,))
    return HttpResponseRedirect(url)


@staff_member_required
@csrf_exempt
@post_required(['payload'])
def ajax_save_preview(request, sheet_id):
    """This method is called by the editor, posting any values that the user
    has changed but have not yet saved into a :class:`Sheet`.  The values are
    stored in a :class:`PreviewSheet` associated with the given
    :class:`Sheet`.

    @param sheet_id: ID of :class`Sheet` object to associate a
        :class:`PreviewSheet` with
    """
    sheet = get_object_or_404(Sheet, id=sheet_id)
    payload = json.loads(request.POST['payload'])
    data = {
        'success':False,
    }

    try:
        preview = PreviewSheet.objects.get(sheet=sheet)
    except PreviewSheet.DoesNotExist:
        preview = PreviewSheet.objects.create(sheet=sheet)

    try:
        preview.store = json.dumps(payload.get('overrides', '{}'))
        preview.save()
        preview.content()   # trigger any compilation errors
        data['success'] = True
        data['preview_url'] = reverse('bseditor-preview-sheet', 
            args=(preview.id,))
    except Exception as e:
        data['msg'] = str(e)

    return JsonResponse(data)
