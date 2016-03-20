import json, os, mock, copy

from django.contrib import messages
from django.test import override_settings
from awl.utils import refetch
from awl.waelsteng import AdminToolsMixin, messages_from_response

from bseditor.conv import ordered_json
from bseditor.models import Version, Sheet, PreviewSheet
from bseditor.tests.sampledata import (EXPECTED_SASS_PREVIEW_FILE,
    SASS_FILE_CUSTOMIZED_DICT, SASS_FILE_OVERRIDES_DICT)

from bseditor.tests.utils import BSEditorTest, create_fakestrap

# ============================================================================
# Test Class
# ============================================================================

class ViewsTest(BSEditorTest, AdminToolsMixin):
    def test_views(self):
        self.initiate()

        compile_filename, variables_filename = create_fakestrap(self.dir_name)
        version = Version.factory('v1', variables_filename, compile_filename)
        sheet = Sheet.factory('s1', version, SASS_FILE_CUSTOMIZED_DICT)

        output_dir = os.path.join(self.dir_name, 'output')
        os.mkdir(output_dir)
        with override_settings(BSEDITOR_DEPLOY_DIR=output_dir):
            # --------------------------
            # -- test ajax_save_sheet
            expected = copy.copy(sheet.get_vars().custom_values)
            expected['body-bg'] = '#aaa'
            payload = {
                'name':sheet.name,
                'custom':expected,
            }
            data = {
                'payload':json.dumps(payload),
            }

            response = self.authed_post(
                '/bseditor/ajax_save_sheet/%s/' % sheet.id, data)

            results = messages_from_response(response)
            self.assertEqual(1, len(results))
            self.assertEqual('Saved & deployed %s' % sheet.filename,
                results[0][0])
            self.assertEqual(messages.SUCCESS, results[0][1])

            sheet = refetch(sheet)
            self.assertEqual(expected, sheet.get_vars().custom_values)

            # force an error when saving to check error handling (error
            # message should be added to existing message queue)
            with mock.patch('bseditor.views.Sheet.save') as patched:
                patched.side_effect = KeyError()

                response = self.silent_authed_post(
                    '/bseditor/ajax_save_sheet/%s/' % sheet.id, data)

                results = messages_from_response(response)
                self.assertEqual(2, len(results))
                self.assertEqual(messages.ERROR, results[1][1])

        # --------------------------
        # -- ajax_colour_value view
        payload = {
            'sass_variable':'gray-base',
            'version':version.id,
            'overrides':{
                'gray-base':'#00f',
            },
        }
        data = { 'payload':json.dumps(payload), }

        response = self.authed_post('/bseditor/ajax_colour_value/', data)
        result = json.loads(response.content.decode('utf-8'))
        self.assertTrue(result['success'])
        self.assertEqual('#00f', result['colours']['gray-base'])
        self.assertEqual('#00f', result['colours']['text-color'])

        # -- ajax_colour_value failure modes

        # bad source in Version, compile error should return success=False
        payload['overrides'] = {}
        data = { 'payload':json.dumps(payload), }
        t = version._store
        mess = ordered_json(version._store)
        mess['sections']['Colors']['components']['gray-base']['value'] = '$foo'
        version._store = json.dumps(mess)
        version.save()

        response = self.authed_post('/bseditor/ajax_colour_value/', data)
        result = json.loads(response.content.decode('utf-8'))
        self.assertFalse(result['success'])

        version._store = t
        version.save()

        # bad dependency in Version should be ignored
        t = version._store
        mess = ordered_json(version._store)
        mess['sections']['Scaffolding']['components']['text-color']['value'] = \
            'foo $gray-base'
        version._store = json.dumps(mess)
        version.save()

        response = self.authed_post('/bseditor/ajax_colour_value/', data)
        result = json.loads(response.content.decode('utf-8'))

        # text-color should not be in result because we messed it up
        self.assertTrue(result['success'])
        self.assertEqual(1, len(result['colours'].keys()))
        self.assertEqual('#000', result['colours']['gray-base'])

        version._store = t
        version.save()

        # missing overrides key in call, should return success=False
        del payload['overrides']
        data = { 'payload':json.dumps(payload), }

        response = self.authed_post('/bseditor/ajax_colour_value/', data)
        result = json.loads(response.content.decode('utf-8'))
        self.assertFalse(result['success'])

        # --------------------------
        # -- preview_css view
        preview = PreviewSheet.factory(sheet, SASS_FILE_OVERRIDES_DICT)
        response = self.authed_get('/bseditor/preview_css/%s/' % preview.id)
        self.assertEqual(EXPECTED_SASS_PREVIEW_FILE,
            response.content.decode('utf-8'))

        # --------------------------
        # -- preview_sheet view
        response = self.authed_get('/bseditor/preview_sheet/%s/' % preview.id)
        self.assertTemplateUsed(response, 'bseditor/preview_sheet.html')

        # --------------------------
        # -- ajax_save_preview view

        # remove any PreviewSheets before first test
        PreviewSheet.objects.filter(sheet=sheet).delete()

        payload = {}
        data = { 'payload':json.dumps(payload), }

        response = self.authed_post(
            '/bseditor/ajax_save_preview/%s/' % preview.id, data)
        result = json.loads(response.content.decode('utf-8'))

        previews = PreviewSheet.objects.filter(sheet=sheet)
        self.assertEqual(1, len(previews))
        self.assertTrue(result['success'])
        self.assertEqual('/bseditor/preview_sheet/%s/' % previews[0].id, 
            result['preview_url'])

        # force an error when saving to check error handling 
        with mock.patch('bseditor.views.PreviewSheet.save') as patched:
            patched.side_effect = KeyError()

            response = self.authed_post(
                '/bseditor/ajax_save_preview/%s/' % sheet.id, data)

            results = messages_from_response(response)
            result = json.loads(response.content.decode('utf-8'))
            self.assertFalse(result['success'])
