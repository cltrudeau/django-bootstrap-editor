import json
from collections import OrderedDict

from django.test import TestCase

from bseditor.conv import BStrapVars, Section, Component

# ============================================================================

def pprint(data):
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
        self.colour_comps = []
        dv = DummyVar()
        self.section1 = Section(dv, 'Colors', 'Gray and brand colors')
        self.comp1_1 = self.section1.add_component('gray-base', '#000')
        self.all_comps.append(self.comp1_1)
        self.colour_comps.append(self.comp1_1)
        self.comp1_2 = self.section1.add_component('gray-darker', 
            'lighten($gray-base, 13.5%)')
        self.all_comps.append(self.comp1_2)
        self.colour_comps.append(self.comp1_2)

        self.section2 = Section(dv, 'Scaffolding', 
            'Settings for some of the most global styles')
        self.comp2_1 = self.section2.add_component('body-bg', '#fff', 
            'Background color for <body>')
        self.all_comps.append(self.comp2_1)
        self.colour_comps.append(self.comp2_1)
        self.comp2_2 = self.section2.add_component('body-font', 'arial')
        self.all_comps.append(self.comp2_2)

        self.sections = OrderedDict()
        self.sections[self.section1.name] = self.section1.to_dict()
        self.sections[self.section2.name] = self.section2.to_dict()

        self.compN_1 = Component('thing', '#333', 'some thing')
        self.all_comps.append(self.compN_1)
        self.colour_comps.append(self.compN_1)
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
        bsv = BStrapVars.factory(self.data)

        # check sections
        expected = [self.section1.name, self.section2.name]
        self.assertEqual(list(bsv.sections.keys()), expected)

        # check all components in sections
        expected = [comp.name for comp in self.all_comps]
        result = [comp.name for comp in bsv.all_components.values()]
        self.assertEqual(result, expected)

        # check colour components
        expected = [comp.name for comp in self.colour_comps]
        result = [comp.name for comp in bsv.colour_components.values()]
        self.assertEqual(result, expected)

        expected = ['#000', '#222222', '#fff', '#333']
        result = [comp.colour_value for comp in bsv.colour_components.values()]
        self.assertEqual(result, expected)

        # check values
        expected = [(comp.name, comp.value) for comp in self.all_comps]
        result = list(bsv.all_value_pairs())
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

        # override some of the custom values
        o = {
            self.comp1_1.name:'#CCC',
            self.compN_2.name:'three',
        }

        expected[0] = (self.comp1_1.name, '#CCC')
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
