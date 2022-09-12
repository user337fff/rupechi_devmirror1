from django import forms
from apps.catalog.models import Product


class WishlistProductForm(forms.Form):
    product = forms.ModelChoiceField(queryset=Product.objects.all())
