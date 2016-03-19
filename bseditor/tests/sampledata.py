import json
from collections import OrderedDict

VARS_FILE = """
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
$text-color:            $gray-base;   // ignore this

//=== Inverted navbar
// Reset inverted navbar basics
$navbar-inverse-bg:                         #222 !default;
"""

VARS_FILE_DICT = OrderedDict([
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

# JSON version of test VARS file
VARS_JSON = json.dumps(VARS_FILE_DICT)

# -----
# bad file for checking error conditions
ERROR_VARS_FILE = """
//== Colors
$gray-base:              #000 !default;
foo: #000;
"""

ERROR_VARS_FILE_DICT = OrderedDict([
    ('sections', OrderedDict([
        ('Colors', OrderedDict([
            ('components', OrderedDict([
                ('gray-base', {'value':'#000'}),
            ])),
        ])),
    ]))
])

# JSON version of test error VARS file
ERROR_VARS_JSON = json.dumps(ERROR_VARS_FILE_DICT)

# -- SASS File for testing
SASS_FILE = """
body {
    background-color: $body-bg;
    color: $text-color;
}

navbar-inverse {
    background-color: $navbar-inverse-bg;
}
"""

SASS_FILE_CUSTOMIZED_DICT = {
    'body-bg':'#f00',
    'navbar-inverse-bg':'#00f',
}

SASS_FILE_OVERRIDES_DICT = {
    'body-bg':'#0f0',
    'navbar-inverse-bg':'',
}

# !!! DO NOT REFORMAT THIS: it is in the style the SASS compiler outputs
EXPECTED_SASS_FILE = \
"""body {
  background-color: #f00;
  color: #000; }

navbar-inverse {
  background-color: #00f; }
"""

EXPECTED_SASS_PREVIEW_FILE = \
"""body {
  background-color: #0f0;
  color: #000; }

navbar-inverse {
  background-color: #222; }
"""
