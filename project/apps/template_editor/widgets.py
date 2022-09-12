from django import forms

class HtmlEditor(forms.Textarea):
    def __init__(self, *args, **kwargs):
        super(HtmlEditor, self).__init__(*args, **kwargs)
        self.attrs['class'] = 'html-editor'

    class Media:
        css = {
            'all': (
                'https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.59.1/codemirror.css',
                'https://codemirror.net/theme/lucario.css',
                '/static/codemirror-5.9/custom.css'
            )
        }
        js = (
            'https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.59.1/codemirror.js',
            'https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.59.1/mode/xml/xml.js',
            # 'https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.59.1/mode/htmlmixed/htmlmixed.js',
            'https://codemirror.net/addon/mode/overlay.js',
            'https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.59.1/mode/django/django.js',
            '/static/codemirror-5.9/init.js'
        )