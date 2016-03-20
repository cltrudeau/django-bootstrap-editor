import json, runpy
from collections import OrderedDict

from django.test import TestCase
from wrench.contexts import temp_file, capture_stdout

from bseditor.conv import BStrapVars, Section, Component
from bseditor.tests.sampledata import (VARS_FILE, VARS_JSON, ERROR_VARS_FILE,
    ERROR_VARS_JSON)

# ============================================================================

def pprint(data):   # pragma: no cover
    print(json.dumps(data, sort_keys=True, indent=4, separators=(',', ': ')))

# ============================================================================
# Test Class
# ============================================================================

class DummyVar(object):
    def __init__(self):
        self.all_components = {}


class BStrapVarsTest(TestCase):
    def setUp(self):
        self.all_comps = []
        self.colour_values = OrderedDict()
        dv = DummyVar()
        self.section1 = Section(dv, 'Colors', 'Gray and brand colors')

        self.comp1_1 = self.section1.add_component('gray-base', '#000')
        self.all_comps.append(self.comp1_1)
        self.colour_values[self.comp1_1.name] = '#000'

        self.comp1_2 = self.section1.add_component('gray-darker', 
            'lighten($gray-base, 13.5%)')
        self.all_comps.append(self.comp1_2)
        self.colour_values[self.comp1_2.name] = '#222222'

        self.comp1_3 = self.section1.add_component('compounded', 
            'lighten($gray-darker, 13.5%)')
        self.all_comps.append(self.comp1_3)
        self.colour_values[self.comp1_3.name] = '#454545'

        self.section2 = Section(dv, 'Scaffolding', 
            'Settings for some of the most global styles')
        self.comp2_1 = self.section2.add_component('body-bg', '#fff', 
            'Background color for <body>')
        self.all_comps.append(self.comp2_1)
        self.colour_values[self.comp2_1.name] = '#fff'
        self.comp2_2 = self.section2.add_component('body-font', 'arial')
        self.all_comps.append(self.comp2_2)

        self.sections = OrderedDict()
        self.sections[self.section1.name] = self.section1.to_dict()
        self.sections[self.section2.name] = self.section2.to_dict()

        self.compN_1 = Component('thing', '#333', 'some thing')
        self.all_comps.append(self.compN_1)
        self.colour_values[self.compN_1.name] = '#333'
        self.compN_2 = Component('other', 'not a colour')
        self.all_comps.append(self.compN_2)
        self.compN_3 = Component('place', 'Egypt')
        self.all_comps.append(self.compN_3)

        self.nonsections = OrderedDict()
        self.nonsections[self.compN_1.name] = self.compN_1.to_dict()
        self.nonsections[self.compN_2.name] = self.compN_2.to_dict()
        self.nonsections[self.compN_3.name] = self.compN_3.to_dict()
        
        self.data = OrderedDict()
        self.data['sections'] = self.sections
        self.data['nonsections'] = self.nonsections

    def test_base(self):
        # check we don't blow up if no data
        BStrapVars.factory({})
        BStrapVars.factory({}, {})
        BStrapVars.factory({}, {}, {})
        BStrapVars.factory('{}')
        BStrapVars.factory('{}', '{}')
        BStrapVars.factory('{}', '{}', '{}')

        # -- test valid data
        bsv = BStrapVars.factory(self.data)

        # check sections
        expected = [self.section1.name, self.section2.name]
        self.assertEqual(list(bsv.sections.keys()), expected)

        # check all components in sections
        expected = [comp.name for comp in self.all_comps]
        result = [comp.name for comp in bsv.all_components.values()]
        self.assertEqual(result, expected)

        # check values
        expected = [(comp.name, comp.value) for comp in self.all_comps]
        result = list(bsv.all_value_pairs())
        self.assertEqual(result, expected)

        # check colour values
        expected = list(self.colour_values.values())
        result = list(bsv.colour_values.values())
        self.assertEqual(result, expected)

        # -- test dependencies
        expected = set([self.comp1_2.name, self.comp1_3.name])
        result = bsv.dependencies(self.comp1_1.name)
        self.assertEqual(result, expected)

        # check something without dependencies
        result = bsv.dependencies(self.comp2_1.name)
        self.assertEqual(result, set([]))

    def test_custom_and_overrides(self):
        c = {
            self.comp1_1.name:'#AAA',
            self.comp2_1.name:'#BBB',
            self.compN_2.name:'one',
            self.compN_3.name:'two',
        }

        bsv = BStrapVars.factory(self.data, c)

        expected = [(comp.name, comp.value) for comp in self.all_comps]
        expected[0] = (self.comp1_1.name, '#AAA')
        expected[3] = (self.comp2_1.name, '#BBB')
        expected[6] = (self.compN_2.name, 'one')
        expected[7] = (self.compN_3.name, 'two')
        result = list(bsv.all_value_pairs())
        self.assertEqual(result, expected)

        c = json.dumps(c)
        bsv = BStrapVars.factory(self.data, c)
        result = list(bsv.all_value_pairs())
        self.assertEqual(result, expected)

        # override some of the custom values, blank override means use default
        o = {
            self.comp1_1.name:'#CCC',
            self.comp2_1.name:'',
            self.compN_2.name:'three',
        }

        expected[0] = (self.comp1_1.name, '#CCC')
        expected[3] = (self.comp2_1.name, '#fff')
        expected[6] = (self.compN_2.name, 'three')

        bsv = BStrapVars.factory(self.data, c, o)
        result = list(bsv.all_value_pairs())
        self.assertEqual(result, expected)

        o = json.dumps(o)
        bsv = BStrapVars.factory(self.data, c, o)
        result = list(bsv.all_value_pairs())
        self.assertEqual(result, expected)

        # test serialization
        expected = BStrapVars.factory(self.data, c)
        expected_base = expected.base_to_json()
        expected_custom = expected.custom_to_json()

        result = BStrapVars.factory(expected_base, expected_custom)
        result_base = result.base_to_json()
        result_custom = result.custom_to_json()

        self.assertEqual(result_base, expected_base)
        self.assertEqual(result_custom, expected_custom)

    def test_file_parse(self):
        # write VARS_FILE into a file that gets cleaned up, then test parsing it
        with temp_file() as filename:
            f = open(filename, 'w')
            f.write(VARS_FILE)
            f.close()

            result = BStrapVars.factory_from_sass_file(filename)
            result_json = result.base_to_json()
            self.assertEqual(VARS_JSON, result_json)

        # test error handling properly ignores bad variables
        with temp_file() as filename:
            f = open(filename, 'w')
            f.write(ERROR_VARS_FILE)
            f.close()

            result = BStrapVars.factory_from_sass_file(filename)
            result_json = result.base_to_json()
            self.assertEqual(ERROR_VARS_JSON, result_json)

    def test_module_main(self):
        # write VARS_FILE into a file that gets cleaned up 
        with capture_stdout(), temp_file() as filename:
            f = open(filename, 'w')
            f.write(VARS_FILE)
            f.close()

            import sys
            keep = sys.argv
            try:
                sys.argv[1] = filename
            except IndexError:
                sys.argv.append(filename)

            runpy.run_module('bseditor.conv', run_name='__main__')
            sys.argv = keep
