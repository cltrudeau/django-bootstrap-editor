import os

from django.test import TestCase
from wrench.contexts import temp_directory
from wrench.logtools.utils import silence_logging

from bseditor.tests.sampledata import SASS_FILE, VARS_FILE

# ============================================================================

class BSEditorTest(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir_cm = temp_directory()
        cls.dir_name = cls.temp_dir_cm.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.temp_dir_cm.__exit__(None, None, None)

    @silence_logging
    def silent_authed_get(self, url, follow=False):
        return self.authed_get(url, follow=follow)

    @silence_logging
    def silent_authed_post(self, url, data, follow=False):
        return self.authed_post(url, data, follow=follow)


def create_fakestrap(dir_name):
    """Creates needed files based on sampledata.py contents to do some testing
    in a Bootstrap-like environment."""
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

    return compile_filename, variables_filename
