import json, runpy
from collections import OrderedDict

from django.test import TestCase
from wrench.contexts import temp_file, capture_stdout

from bseditor.conv import BStrapVars, Section, Component

# ============================================================================

def pprint(data):   # pragma: no cover
    print(json.dumps(data, sort_keys=True, indent=4, separators=(',', ': ')))

# ============================================================================

SASS_FILE = """
$bootstrap-sass-asset-helper: false !default;
// --------------------------------------------------

//== Colors
//
//## Gray and brand colors for use across Bootstrap.

$gray-base:              #000 !default;

//== Scaffolding
//
//## Settings for some of the most global styles.

//** Background color for `<body>`.
$body-bg:               #fff !default;
//** Global text color on `<body>`.
$text-color:            $gray-base   // ignore this

//=== Inverted navbar
// Reset inverted navbar basics
$navbar-inverse-bg:                         #222 !default;
"""

SASS_FILE_DICT = OrderedDict([
    ('sections', OrderedDict([
        ('Colors', OrderedDict([
            ('components', OrderedDict([
                ('gray-base', {'value':'#000'}),
            ])),
            ('info', 'Gray and brand colors for use across Bootstrap.'),
        ])),
        ('Scaffolding', OrderedDict([
            ('components', OrderedDict([
                ('body-bg', OrderedDict([
                    ('info', 'Background color for `<body>`.'),
                    ('value', '#fff'),
                ])),
                ('text-color', OrderedDict([
                    ('info', 'Global text color on `<body>`.'),
                    ('value', '$gray-base'),
                ]))
            ])),
            ('info', 'Settings for some of the most global styles.'),
        ])),
        ('Inverted navbar', OrderedDict([
            ('components', OrderedDict([
                ('navbar-inverse-bg', {'value':'#222'}),
            ])),
        ])),
    ]))
])

# JSON version of test SASS file
SASS_JSON = json.dumps(SASS_FILE_DICT)

# -----
# bad file for checking error conditions
ERROR_SASS_FILE = """
//== Colors
$gray-base:              #000 !default;
foo: #000;
"""

ERROR_SASS_FILE_DICT = OrderedDict([
    ('sections', OrderedDict([
        ('Colors', OrderedDict([
            ('components', OrderedDict([
                ('gray-base', {'value':'#000'}),
            ])),
        ])),
    ]))
])

# JSON version of test error SASS file
ERROR_SASS_JSON = json.dumps(ERROR_SASS_FILE_DICT)

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
        self.colour_values[self.comp1_1] = '#000'
        self.comp1_2 = self.section1.add_component('gray-darker', 
            'lighten($gray-base, 13.5%)')
        self.all_comps.append(self.comp1_2)
        self.colour_values[self.comp1_2] = '#000'

        self.section2 = Section(dv, 'Scaffolding', 
            'Settings for some of the most global styles')
        self.comp2_1 = self.section2.add_component('body-bg', '#fff', 
            'Background color for <body>')
        self.all_comps.append(self.comp2_1)
        self.colour_values[self.comp2_1] = '#fff'
        self.comp2_2 = self.section2.add_component('body-font', 'arial')
        self.all_comps.append(self.comp2_2)

        self.sections = OrderedDict()
        self.sections[self.section1.name] = self.section1.to_dict()
        self.sections[self.section2.name] = self.section2.to_dict()

        self.compN_1 = Component('thing', '#333', 'some thing')
        self.all_comps.append(self.compN_1)
        self.colour_values[self.compN_1] = '#333'
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
        expected = ['#000', '#222222', '#fff', '#333']
        result = list(bsv.colour_values.values())
        self.assertEqual(result, expected)

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
        expected[2] = (self.comp2_1.name, '#BBB')
        expected[5] = (self.compN_2.name, 'one')
        expected[6] = (self.compN_3.name, 'two')
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
        expected[2] = (self.comp2_1.name, '#fff')
        expected[5] = (self.compN_2.name, 'three')

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
        # write SASS_FILE into a file that gets cleaned up 
        with temp_file() as filename:
            f = open(filename, 'w')
            f.write(SASS_FILE)
            f.close()

            result = BStrapVars.factory_from_sass_file(filename)
            result_json = result.base_to_json()
            self.assertEqual(SASS_JSON, result_json)

        # test error handling properly ignores bad variables
        with temp_file() as filename:
            f = open(filename, 'w')
            f.write(ERROR_SASS_FILE)
            f.close()

            result = BStrapVars.factory_from_sass_file(filename)
            result_json = result.base_to_json()
            self.assertEqual(ERROR_SASS_JSON, result_json)

    def test_module_main(self):
        # write SASS_FILE into a file that gets cleaned up 
        with capture_stdout():
            with temp_file() as filename:
                f = open(filename, 'w')
                f.write(SASS_FILE)
                f.close()

                import sys
                keep = sys.argv
                try:
                    sys.argv[1] = filename
                except IndexError:
                    sys.argv.append(filename)

                runpy.run_module('bseditor.conv', run_name='__main__')
                sys.argv = keep
