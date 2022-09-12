from django import forms

from apps.catalog.models import Product
from apps.domains.middleware import get_request


class FixGlobalRequest(forms.Form):
    product = forms.ModelChoiceField(queryset=Product.objects.none())

    def __init__(self, *args, **kwargs):
        super(FixGlobalRequest, self).__init__(*args, **kwargs)
        # Необходимо переопределить т.к. глобальный реквест до формирования формы пустой
        self.fields['product'].queryset = Product.objects.active()

    def clean(self):
        data = self.cleaned_data
        domain = get_request().domain
        data['option'] = domain
        return data


class CartQuantityProductForm(FixGlobalRequest):
    quantity = forms.IntegerField()


class CartDeleteProductForm(FixGlobalRequest):
    pass
