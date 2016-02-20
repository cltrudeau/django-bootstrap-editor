import re, sass, json
from collections import OrderedDict

from six import string_types

from awl.css_colours import is_colour

# ============================================================================
# Container Classes
# ============================================================================

class Component(object):
    def __init__(self, name, value, info=''):
        self.name = name
        self.info = info
        self.colour_value = ''

        # normalize value to the bare portion we use
        value = value.strip()
        i = value.find('!default')
        if i > -1:
            value = value[0:i - 1] + value[i + 8:]

        i = value.find(';')
        if i > -1:
            value = value[0:i]

        i = value.find('//')
        if i > -1:
            value = value[0:i]

        self.value = value.strip()

    def to_dict(self):
        d = OrderedDict()
        if self.info:
            d['info'] = self.info

        if self.value:
            d['value'] = self.value

        return d


class Section(object):
    def __init__(self, parent, name, info=''):
        self.parent = parent
        self.name = name
        self.components = OrderedDict()
        self.info = info

    def add_component(self, name, value, info=''):
        comp = Component(name, value, info)
        self.parent.all_components[name] = comp
        self.components[name] = comp
        return comp

    def to_dict(self):
        """Creates and returns copy of the Section as a dictionary"""
        d = OrderedDict()

        if self.components:
            d['components'] = OrderedDict()
        for comp in self.components.values():
            d['components'][comp.name] = comp.to_dict()

        if self.info:
            d['info'] = self.info


        return d


class BStrapVars(object):
    # -- CSS matching expression
    #
    # Typical pattern to match:
    #
    #  .component-offset-horizontal {
    #     color: 180px; }
    #
    css_pieces = re.compile(
        """
        \.                # starts with period
        ([^\s]*)          # css class name everything up to white space
        [^:]*:            # eat everything up to first ":"
        \s*               # eat whitespace
        ([^;]*)           # value is everything up to first ";"
        .*\}              # eat everything up to the closing }
        """, re.VERBOSE)

    def __init__(self):
        self.sections = OrderedDict()
        self.nonsections = OrderedDict()
        self.all_components = OrderedDict()
        self.colour_components = OrderedDict()

        self.custom = OrderedDict()
        self.overrides = OrderedDict()

    @classmethod
    def factory(cls, base, custom=None, overrides=None):
        """
        Constructs a BootStrap Sass variables container that stores three
        types of data: default base variables for BootStrap Sass ordered by
        sections, optional sets of customizations and optional overrides.

        Priority of items in the container work as follows:

        * items in the override list that are non-empty
        * items in the override list that are empty return the same item from
        the base (i.e. ignores any customizations)
        * items in the customs list
        * items in the base

        No items in the custom list should be empty.

        Serialized base vars are stored as an OrderedDict with two keys:
        'sections' and 'nonsections'.  The 'nonsections' area contains
        dictionaries of variables: their values and any associated info.  This
        is for any BootStrap vars that are not stored in a section (BootStrap
        v3 keeps everything in sections).  The 'sections' area is an
        OrderedDict with each key being the name of the section mapping to a
        dict containing 'info' and another OrderedDict of components.

        Example:

        .. code-block:: python

            d = OrderedDict(
                ('sections', OrderedDict(
                    ('Colors', {
                        'info':Gray and brand colors',
                        'components':OrderedDict(
                            ('gray-base', {
                                'value':'#000',
                            }),
                            ('gray-darker', {
                                'value':'lighten($gray-base, 13.5%)',
                            }),
                        ),
                    }),
                    ('Scaffolding', {
                        'info':Settings for some of the most global styles',
                        'components':OrderedDict(
                            ('body-bg', {
                                'value':'#fff',
                                'info':'Background color for <body>',
                            }),
                        ),
                    }),
                )),
                ('nonsections', OrderedDict(
                    ('thing', {
                        'value':'#333',
                        'info':'some thing',
                    })
                )),
            )

        :param base: an OrderedDict of the base set of variables in serialized
            storage form for the Bootstrap or a string containing a JSON
            representation of same
        :param custom: a dict of name/value pairs of custom values to
            use instead of those found in the base or a JSON reprsentation of
            same
        :param overrides: a dict of name/value pairs 
        """
        bstrap_vars = BStrapVars()

        # handle both JSON strings and dictionaries
        if isinstance(base, string_types):
            base = json.loads(base, object_pairs_hook=OrderedDict)

        for name, section_enc in base['sections'].items():
            info = section_enc.get('info', '')
            section = bstrap_vars.add_section(name, info)
            for comp_name, comp in section_enc['components'].items():
                info = comp.get('info', '')
                section.add_component(comp_name, comp['value'], info)

        for name, comp in base['nonsections'].items():
            info = comp.get('info', '')
            bstrap_vars.add_component(name, comp['value'], info)

        if isinstance(custom, string_types):
            custom = json.loads(custom, object_pairs_hook=OrderedDict)

        if isinstance(overrides, string_types):
            overrides = json.loads(overrides, object_pairs_hook=OrderedDict)

        if custom:
            bstrap_vars.custom = custom

        if overrides:
            bstrap_vars.overrides = overrides

        bstrap_vars.detect_types()
        return bstrap_vars

    @classmethod
    def factory_from_sass_file(cls, filename):
        """A factory for BStrapVars that uses a Bootstrap SASS definition file
        to construct the information.
        """
        bsvars = BStrapVars()

        with open(filename) as f:
            section = None
            next_info = ''
            for count, line in enumerate(f):
                line = line.strip()
                if not line:
                    continue

                if line.startswith('//==='):
                    name = line[5:].strip()
                    section = bsvars.add_section(name)
                elif line.startswith('//=='):
                    name = line[4:].strip()
                    section = bsvars.add_section(name)
                elif line.startswith('//##'):
                    info = line[4:].strip()
                    section.info = info
                elif line.startswith('//**'):
                    info = line[4:].strip()
                    next_info = info
                else:
                    if not section:
                        # no section defined yet, ignore line
                        continue

                    try:
                        name, value = line.split(':')
                        if name[0] != '$':
                            raise ValueError
                    except ValueError:
                        # something has gone wrong, ignore the line
                        continue

                    name = name[1:]
                    component = section.add_component(name, value, next_info)
                    bsvars.all_components[name] = component
                    next_info = ''

        # file parsed, process found data for more info
        bsvars.detect_types()
        return bsvars

    def base_to_json(self):
        """Serializes the base value variables into JSON."""
        d = OrderedDict()
        if self.sections:
            d['sections'] = OrderedDict()

            for section in self.sections.values():
                d['sections'][section.name] = section.to_dict()

        if self.nonsections:
            d['nonsections'] = OrderedDict()

            for comp in self.nonsections.values():
                d['nonsections'][comp.name] = comp.to_dict()

        return json.dumps(d)

    def custom_to_json(self):
        """Serializes the custom component pieces to JSON."""
        return json.dumps(self.custom)
        
    def add_section(self, name, info=''):
        """Creates a new Section and associates it with this object.

        :param name: name of the section
        :param info: [optional] info blurb about the section, defaults to
            empty
        """
        section = Section(self, name, info)
        self.sections[name] = section
        return section

    def add_component(self, name, value, info=''):
        """Creates a new Component that is not associated with a Section and
        associates it with this object.

        :param name: name of the component
        :param value: value to be contained in the new component
        :param info: [optional] info blurb about the component, defaults to
            empty
        """
        component = Component(name, value, info)
        self.nonsections[name] = component
        self.all_components[name] = component
        return component

    def get_value(self, name):
        if name in self.overrides:
            value = self.overrides[name]
            if value:
                return value
            else:
                # empty override, which means we use the default value not the
                # custom value
                return self.all_components[name].value

        if name in self.custom:
            return self.custom[name]

        return self.all_components[name].value

    def all_value_pairs(self):
        """Returns an ordered iterator of name/value pairs in the
        components."""
        for comp in self.all_components.values():
            yield (comp.name, self.get_value(comp.name))

    def detect_types(self):
        # uses the sass compiler to create fake CSS classes in order to
        # evaluate the expressions in each component.value, detects those that
        # are colours and puts the detected value in the component
        src = ['$bootstrap-sass-asset-helper:false;']
        for name, component in self.all_components.items():
            src.append('$%s:%s;' % (name, component.value))
            src.append('.%s{color:%s}' % (name, component.value))

        #with open('last_compile.txt', 'w') as f:
        #    f.write('\n'.join(src))

        result = sass.compile(string='\n'.join(src))
        for match in self.css_pieces.finditer(result):
            name = match.group(1)
            value = match.group(2).strip()
            if is_colour(value):
                self.all_components[name].colour_value = value
                self.colour_components[name] = self.all_components[name]

# ============================================================================
# Parser
# ============================================================================

if __name__ == '__main__':
    import sys
    print('=====>', sys.argv[1])
    bsv = BStrapVars.factory_from_sass_file(sys.argv[1])

    print('=====================================')
    for name, section in bsv.sections.items():
        print(name + ':')
        for comp_name, comp in section.components.items():
            print('   %s:*%s*' % (comp_name, comp.value))
            if comp.info:
                print('      ->', comp.info)

    print('=====================================')
    print('==         Colours                 ==')
    print('=====================================')
    for name, component in bsv.colour_components.items():
        print(name)
        print('   ' + component.value)
        print('   =>' + component.colour_value)

    print('=====================================')
    print('==          BASE JSON              ==')
    print('=====================================')
    print(bsv.base_to_json())
