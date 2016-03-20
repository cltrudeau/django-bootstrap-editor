import os, mock

from django.contrib import messages
from django.test import override_settings
from awl.waelsteng import AdminToolsMixin, messages_from_response
from wrench.utils import parse_link

from bseditor.admin import VersionAdmin, SheetAdmin
from bseditor.conv import ordered_json
from bseditor.models import Version, Sheet, PreviewSheet
from bseditor.tests.sampledata import (VARS_JSON, EXPECTED_SASS_FILE,
    EXPECTED_SASS_PREVIEW_FILE, SASS_FILE_CUSTOMIZED_DICT,
    SASS_FILE_OVERRIDES_DICT)

from bseditor.tests.utils import BSEditorTest, create_fakestrap

# ============================================================================
# Test Class
# ============================================================================

class GotHereError(Exception):
    pass


def fake_deploy_hook(self):
    raise GotHereError


class ModelsTest(BSEditorTest, AdminToolsMixin):
    def test_models(self):
        self.initiate()

        compile_filename, variables_filename = create_fakestrap(self.dir_name)
        version = Version.factory('v1', variables_filename, compile_filename)

        # verify load/compile worked
        self.assertEqual(version._store, VARS_JSON)

        # -- test Version Admin
        version_admin = VersionAdmin(Version, self.site)

        links = self.field_value(version_admin, version, 'show_actions')
        show, create = links.split(',')

        # test Show Vars link
        url, text = parse_link(show)
        self.assertEqual('Show Variables', text)
        expected = ordered_json(version.get_vars().base_to_json())
        response = self.authed_get(url)
        result = ordered_json(response.content.decode('utf-8'))
        self.assertEqual(expected, result)

        # test Create Sheet link
        url, text = parse_link(create)
        self.assertEqual('Create Sheet', text)
        self.authed_get(url, response_code=302)
        sheets = Sheet.objects.all()
        self.assertEqual(1, len(sheets))
        self.assertEqual(version, sheets[0].version)
        self.assertEqual('new sheet', sheets[0].name)

        # do it again, check the sheet name incrementer
        self.authed_get(url, response_code=302)
        sheets = Sheet.objects.all()
        self.assertEqual(2, len(sheets))
        self.assertEqual('new sheet 1', sheets[1].name)

        # -- test Sheet
        output_dir = os.path.join(self.dir_name, 'output')
        os.mkdir(output_dir)

        with override_settings(BSEDITOR_DEPLOY_DIR=output_dir,
                BSEDITOR_TRACK_LAST_COMPILE=True):
            sheet = Sheet.factory('s1', version, SASS_FILE_CUSTOMIZED_DICT)
            self.assertEqual('s1.css', sheet.filename)

            # check states before we deploy
            sheet_admin = SheetAdmin(Sheet, self.site)
            result = self.field_value(sheet_admin, sheet, 'show_filedate')
            self.assertEqual('<i>no file</i>', result)

            expected = os.path.join(output_dir, 's1.css')
            self.assertEqual(expected, sheet.full_filename)
            self.assertEqual(None, sheet.last_deploy)

            # -- test deployment
            sheet.deploy()

            # check states after deploy
            result = self.field_value(sheet_admin, sheet, 'show_filedate')
            self.assertEqual(sheet.last_deploy, result)

            # check last compile record is there
            fname = os.path.join(output_dir, 'last_compile.txt')
            os.path.isfile(fname)

            # verify the created CSS file
            fname = os.path.join(output_dir, 's1.css')
            with open(fname) as f:
                result = f.read()

            self.assertEqual(EXPECTED_SASS_FILE, result)
            self.assertNotEqual(None, sheet.last_deploy)

            # -- test deployment hooks
            hook = 'bseditor.tests.test_models.fake_deploy_hook'
            with override_settings(BSEDITOR_COLLECT_ON_DEPLOY=True):

                # check with custom hook
                with override_settings(BSEDITOR_COLLECT_HOOK=hook):
                    with self.assertRaises(GotHereError):
                        sheet.deploy()

                # check with default hook
                #call_command = 'django.core.management.call_command'
                call_command = 'bseditor.models.call_command'
                with mock.patch(call_command) as patched:
                    sheet.deploy()
                    self.assertTrue(patched.called)
                    self.assertEqual(patched.call_args, (('collectstatic',
                        '--noinput'), ))

            # -- test SheetAdmin
            links = self.field_value(sheet_admin, sheet, 'show_actions')
            edit, preview, deploy = links.split(',')

            # test Edit link
            url, text = parse_link(edit)
            self.assertEqual('Edit', text)
            response = self.authed_get(url)
            self.assertTemplateUsed(response, 'bseditor/edit_sheet.html')

            # test Preview link
            self.assertEqual(0, PreviewSheet.objects.count())

            url, text = parse_link(preview)
            self.assertEqual('Preview', text)
            self.authed_get(url, response_code=302)
            previews = PreviewSheet.objects.all()
            self.assertEqual(1, len(previews))
            self.assertEqual(sheet, previews[0].sheet)

            # do it again, last time created it, this time should fetch it
            self.authed_get(url, response_code=302)
            previews = PreviewSheet.objects.all()
            self.assertEqual(1, len(previews))
            self.assertEqual(sheet, previews[0].sheet)

            # test Deploy link
            url, text = parse_link(deploy)
            self.assertEqual('Deploy', text)
            response = self.authed_get(url, follow=True)
            results = messages_from_response(response)
            self.assertEqual(1, len(results))
            self.assertEqual('Deployed s1.css', results[0][0])
            self.assertEqual(messages.SUCCESS, results[0][1])

            # retest with simulated problem
            with mock.patch('bseditor.views.Sheet.deploy') as patched:
                patched.side_effect = KeyError()
                response = self.silent_authed_get(url, follow=True)

                results = messages_from_response(response)
                self.assertEqual(1, len(results))
                self.assertEqual(messages.ERROR, results[0][1])

        # -- test PreviewSheet
        preview = PreviewSheet.factory(sheet, SASS_FILE_OVERRIDES_DICT)
        self.assertEqual(EXPECTED_SASS_PREVIEW_FILE, preview.content())

        # -- misc coverage tests
        Sheet.factory('s2', version)
        version.get_vars()
        str(version)
        str(sheet)
        str(preview)
