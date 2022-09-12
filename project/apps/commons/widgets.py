from django import forms


class MultiImageField(forms.FileInput):
    template_name = 'commons/widgets/multi_image.html'
    attrs = {'multiple': 'multiple'}


class EditImageWidget(forms.ImageField):
    template_name = 'commons/widgets/multi_image.html'
    attrs = {'multiple': 'multiple'}
