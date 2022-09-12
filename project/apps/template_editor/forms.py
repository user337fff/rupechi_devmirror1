from django import forms
from django.conf import settings
from .widgets import HtmlEditor
from .finder import template_list, TemplateFinder


TEMPLATE_PATH_CHOICES = []
for path in template_list:
    template_name = TemplateFinder.trim_pre_path(path)
    TEMPLATE_PATH_CHOICES.append((template_name, template_name))


class TemplateForm(forms.Form):
    template_content = forms.CharField(
        label='Редактор',
        widget=HtmlEditor(attrs={'style': 'width: 90%; height: 100%;'}))
    
    template = forms.ChoiceField(
        label='Шаблон',
        choices=TEMPLATE_PATH_CHOICES,
        required=True,
        widget=forms.Select(attrs={'style' : 'width: 200px;'}))
