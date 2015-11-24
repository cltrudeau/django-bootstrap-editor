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

from .conv import SassVariables
from .models import Sheet, Version

logger = logging.getLogger(__name__)

# ============================================================================

@staff_member_required
def show_version_variables(request, version_id):
    version = get_object_or_404(Version, id=version_id)

    # use HttpResponse rather than JsonResponse as we don't want to perform
    # the json.dumps() call, SassVariables must do conversion as it has a
    # specialized encoder
    return HttpResponse(content=version.sass_variables.to_json(), 
        content_type='application/json')


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


@staff_member_required
def edit_sheet(request, sheet_id):
    sheet = get_object_or_404(Sheet, id=sheet_id)

    data = {
        'sheet':sheet,
        'sass_base':sheet.version.sass_variables,
        'sass_custom':sheet.sass_variables,
        'cancel_url':reverse('admin:bseditor_sheet_changelist'),
        'ajax_colour_value_url':reverse('bseditor-ajax-colour-value'),
        'ajax_save_sheet':reverse('bseditor-ajax-save-sheet', args=(sheet.id,)),
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
        sheet.variables = json.dumps(payload['overrides'])
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
    content = json.loads(version.variables, object_pairs_hook=OrderedDict)
    data = {
        'success':False,
    }

    try:
        all_variables = SassVariables.factory_from_dict(content,
            payload['overrides'])
        result = all_variables.all_components[sass_variable].colour_value
        if result:
            data['colour'] = result
            data['success'] = True
    except (sass.CompileError, KeyError):
        # compilation errors, key errors, all should result in the default
        # "success:False" in response
        pass

    return JsonResponse(data)


@staff_member_required
def preview_sheet(request, sheet_id):
    sheet = get_object_or_404(Sheet, id=sheet_id)

    data = {
        'sheet':sheet,
    }

    return render_page(request, 'bseditor/preview_sheet.html', data)


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
