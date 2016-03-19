import json, os, mock

from django.test import TestCase, override_settings
from wrench.contexts import temp_directory

from bseditor.models import Version, Sheet, PreviewSheet
from bseditor.tests.sampledata import (SASS_FILE, EXPECTED_SASS_FILE, 
    EXPECTED_SASS_PREVIEW_FILE, SASS_FILE_CUSTOMIZED_DICT,
    SASS_FILE_OVERRIDES_DICT, VARS_FILE, VARS_JSON)

# ============================================================================

def pprint(data):   # pragma: no cover
    print(json.dumps(data, sort_keys=True, indent=4, separators=(',', ': ')))

# ============================================================================
# Test Class
# ============================================================================

class GotHereError(Exception):
    pass


def fake_deploy_hook(self):
    raise GotHereError


class ModelsTest(TestCase):
    def test_models(self):
        with temp_directory() as dir_name:
            # create a fake bootstrap file
            fakestrap_filename = os.path.join(dir_name, '_fakestrap.scss')
            with open(fakestrap_filename, 'w') as f:
                f.write(VARS_FILE)
                f.write(SASS_FILE)

            # create a custom file -- this will be the one that gets prepended
            # with our populated variables from the Sheet and then imports the
            # fake bootstrap file and compiled
            compile_filename = os.path.join(dir_name, 'compile.sass')
            with open(compile_filename, 'w') as f:
                f.write('@import "fakestrap"\n')

            # create a variables file -- this gets parsed and is the basis for
            # our Version and Sheet objects
            variables_filename = os.path.join(dir_name, '_variables.scss')
            with open(variables_filename, 'w') as f:
                f.write(VARS_FILE)

            version = Version.factory('v1', variables_filename, 
                compile_filename)

            # verify load/compile worked
            self.assertEqual(version._store, VARS_JSON)

            # -- test Sheet
            output_dir = os.path.join(dir_name, 'output')
            os.mkdir(output_dir)

            with override_settings(BSEDITOR_DEPLOY_DIR=output_dir,
                    BSEDITOR_TRACK_LAST_COMPILE=True):
                sheet = Sheet.factory('s1', version, SASS_FILE_CUSTOMIZED_DICT)
                self.assertEqual('s1.css', sheet.filename)

                expected = os.path.join(output_dir, 's1.css')
                self.assertEqual(expected, sheet.full_filename)

                self.assertEqual(None, sheet.last_deploy)

                # -- test deployment
                sheet.deploy()

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

                # -- test PreviewSheet
                preview = PreviewSheet.factory(sheet, SASS_FILE_OVERRIDES_DICT)
                self.assertEqual(EXPECTED_SASS_PREVIEW_FILE, preview.content())

                # -- misc coverage tests
                Sheet.factory('s2', version)
                version.get_vars()
                str(version)
                str(sheet)
                str(preview)
