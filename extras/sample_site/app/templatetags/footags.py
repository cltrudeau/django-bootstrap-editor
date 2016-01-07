from django import template

register = template.Library()

@register.tag
def accessor(parser, token):
    try:
        contents = token.split_contents()
        print('**** %s', contents)
    except ValueError:
        raise template.TemplateSyntaxError('fuck')

    return ThingNode(contents)


class ThingNode(template.Node):
    def __init__(self, format_string):
        self.format_string = format_string

    def render(self, context):
        return 'foo'
