# create_test_data.py
from collections import OrderedDict
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from dform.models import Survey, AnswerGroup
from dform.fields import (Text, MultiText, Dropdown, Radio, Checkboxes,
    Rating, Integer, Float)

# =============================================================================

colours = [ 'Pink', 'LightPink', 'HotPink', 'DeepPink', 'PaleVioletRed', 
    'MediumVioletRed', 'LightSalmon', 'Salmon', 'DarkSalmon', 'LightCoral',
    'IndianRed', 'Crimson', 'FireBrick', 'DarkRed', 'Red', 'OrangeRed',
    'Tomato', 'Coral', 'DarkOrange', 'Orange', 'Yellow', 'LightYellow',
    'LemonChiffon', 'LightGoldenrodYellow', 'PapayaWhip', 'Moccasin',
    'PeachPuff', 'PaleGoldenrod', 'Khaki', 'DarkKhaki', 'Gold', 'Cornsilk',
    'BlanchedAlmond', 'Bisque', 'NavajoWhite', 'Wheat', 'BurlyWood', 'Tan',
    'RosyBrown', 'SandyBrown', 'Goldenrod', 'DarkGoldenrod', 'Peru',
    'Chocolate', 'SaddleBrown', 'Sienna', 'Brown', 'Maroon', 'DarkOliveGreen',
    'Olive', 'OliveDrab', 'YellowGreen', 'LimeGreen', 'Lime', 'LawnGreen',
    'Chartreuse', 'GreenYellow', 'SpringGreen', 'MediumSpringGreen',
    'LightGreen', 'PaleGreen', 'DarkSeaGreen', 'MediumSeaGreen', 'SeaGreen',
    'ForestGreen', 'Green', 'DarkGreen', 'MediumAquamarine', 'Aqua', 'Cyan',
    'LightCyan', 'PaleTurquoise', 'Aquamarine', 'Turquoise',
    'MediumTurquoise', 'DarkTurquoise', 'LightSeaGreen', 'CadetBlue',
    'DarkCyan', 'Teal', 'LightSteelBlue', 'PowderBlue', 'LightBlue',
    'SkyBlue', 'LightSkyBlue', 'DeepSkyBlue', 'DodgerBlue', 'CornflowerBlue',
    'SteelBlue', 'RoyalBlue', 'Blue', 'MediumBlue', 'DarkBlue', 'Navy',
    'MidnightBlue', 
]

class Command(BaseCommand):
    def handle(self, *args, **options):
        survey = Survey.objects.create(name='Sample Survey',
            success_redirect='/admin/')
        survey.add_question(Text, 'Single line text question')
        survey.add_question(MultiText, 'Multiline question', required=True)
        survey.add_question(Dropdown, 'Favourite fruit', 
            field_parms=OrderedDict([('a','Apple'), ('b','Banana'), 
                ('k','Kiwi')]))
        survey.add_question(Radio, 'Planet', 
            field_parms=OrderedDict([('e','Earth'), ('m','Mars')]))
        survey.add_question(Checkboxes, 'Choose all that apply',
            field_parms=OrderedDict([('a','Audi'), ('b','BMW'), 
                ('v','Volkswagon')]))
        survey.add_question(Rating, 'Rate our service')

        survey.add_question(Integer, 'Pick an integer number')
        survey.add_question(Float, 'Pick a float number')

        survey = Survey.objects.create(name='Favourites Survey', 
            success_redirect='/admin/')
        q = survey.add_question(Text, 'What is your favourite colour?')
        
        # generate some answers
        for colour in colours:
            group = AnswerGroup.objects.create(
                survey_version=survey.latest_version)
            survey.answer_question(q, group, colour)

        survey.new_version()
        q2 = survey.add_question(Text, 
            'What is your favourite way of spelling "favourite"?')

        group = AnswerGroup.objects.create(survey_version=survey.latest_version)
        survey.answer_question(q, group, colour[0])
        survey.answer_question(q2, group, 'favourite')

        user = User.objects.first()
        group = AnswerGroup.objects.create(survey_version=survey.latest_version,
            group_data=user)
        survey.answer_question(q, group, colour[1])
        survey.answer_question(q2, group, 'with the "u"')

        survey.new_version()
