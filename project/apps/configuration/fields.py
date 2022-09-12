from django.db import models
class ImageEdit(models.ImageField):
    def formfield(self, **kwargs):
        defaults = {'form_class': MyFormField}
        defaults.update(kwargs)
        return super().formfield(**defaults)