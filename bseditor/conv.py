import re, sass, json
from collections import OrderedDict

from django.utils.text import slugify

from awl.css_colours import is_colour

# ============================================================================
# Container Classes
# ============================================================================

class Component(object):
    def __init__(self, name, value, info=''):
        self.name = name
        self.info = info
        self.colour_value = ''

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

        self.value = value

    @property
    def slug(self):
        return slugify(self.name)


class Section(object):
    def __init__(self, name):
        self.name = name
        self.components = OrderedDict()
        self.info = ''

    def add_component(self, name, value, info=''):
        comp = Component(name, value, info)
        self.components[name] = comp
        return comp

    @property
    def slug(self):
        return slugify(self.name)


class SassEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Section):
            enc = {
                'name':obj.name,
                'components':OrderedDict(),
                'info':obj.info,
            }
            for name, component in obj.components.items():
                enc['components'][name] = {
                    'name':name,
                    'info':component.info,
                    'value':component.value,
                    'colour_value':component.colour_value,
                }

            return enc

        return json.JSONEncoder.default(self, obj)


class SassVariables(object):
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
        self.all_components = OrderedDict()
        self.colour_components = OrderedDict()

    @classmethod
    def factory_from_sass_file(cls, filename):
        variables = SassVariables()
        variables.parse_sass_file(filename)
        return variables

    @classmethod
    def factory_from_dict(cls, content, overrides={}):
        variables = SassVariables()

        for section_enc in content.values():
            section = variables.add_section(section_enc['name'])
            section.info = section_enc['info']
            for comp_enc in section_enc['components'].values():
                name = comp_enc['name']

                component = section.add_component(name, comp_enc['value'], 
                    comp_enc['info'])
                variables.all_components[name] = component

        for key, value in overrides.items():
            if key in variables.all_components:
                variables.all_components[key].value = value
            else:
                variables.add_component(key, value)

        variables.detect_types()
        return variables

    @classmethod
    def factory_from_json(cls, content):
        d = json.loads(content, object_pairs_hook=OrderedDict)
        return cls.factory_from_dict(d)

    def to_json(self):
        return json.dumps(self.sections, cls=SassEncoder)

    def add_section(self, name):
        section = Section(name)
        self.sections[name] = section
        return section

    def add_component(self, name, value, info=''):
        # add a component that is not in a section
        comp = Component(name, value, info)
        self.all_components[name] = comp
        return comp

    def parse_sass_file(self, filename):
        with open(filename) as f:
            section = None
            next_info = ''
            for count, line in enumerate(f):
                line = line.strip()
                if not line:
                    continue

                if line.startswith('//==='):
                    name = line[5:].strip()
                    section = self.add_section(name)
                elif line.startswith('//=='):
                    name = line[4:].strip()
                    section = self.add_section(name)
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
                    self.all_components[name] = component
                    next_info = ''

        # file parsed, process found data for more info
        self.detect_types()

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
    sass_values = SassVariables.factory_from_sass_file(sys.argv[1])

    print('=====================================')
    for name, section in sass_values.sections.items():
        print(name + ':')
        for comp_name, comp in section.components.items():
            print('   %s:*%s*' % (comp_name, comp.value))
            if comp.info:
                print('      ->', comp.info)

    print('=====================================')
    print('==         Colours                 ==')
    print('=====================================')
    for name, component in sass_values.colour_components.items():
        print(name)
        print('   ' + component.value)
        print('   =>' + component.colour_value)

    print('=====================================')
    print('==            JSON                 ==')
    print('=====================================')
    print(sass_values.to_json())
