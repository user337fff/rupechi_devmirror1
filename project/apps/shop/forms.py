from django.forms import ModelForm, forms

from .models import Order
from ..domains.middleware import get_request
from django.db.models import Q
from apps.catalog.models import get_contractor


class OrderForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super(OrderForm, self).__init__(*args, **kwargs)
        request = get_request()
        domain = request.domain
        contractor = 'price' + get_contractor(request)

        if self.fields.get('delivery'):
            self.fields['delivery'].queryset = self.fields['delivery'].queryset\
                .filter(domain__exact=domain)\
                .filter(Q(type_price__title__exact=contractor) | Q(type_price__isnull=True))

        if self.fields.get('payment'):
            self.fields['payment'].queryset = self.fields['payment'].queryset\
                .filter(domain__exact=domain)\
                .filter(Q(type_price__title__exact=contractor) | Q(type_price__isnull=True))

    class Meta:
        model = Order
        fields = ['name', 'phone', 'email', 'delivery', 'store', 'payment', 'comment', 'address']

    def clean(self):
        data = self.cleaned_data
        store = data.get('store')

        print("Cleaned data", data)

        if delivery := data.get('delivery'):
            if delivery.stores.exists():
                if store:
                    store = delivery.stores.filter(id=store.id).first()
                if not store:
                    raise forms.ValidationError({'store': 'Укажите значение из списка'})
                else:
                    data['address'] = ''
                # else:
                #     data['address'] = f'{store.domain.name}, {store.address}'
            else:
                if not data.get('address'):
                    raise forms.ValidationError({'address': 'Укажите адрес'})
                else:
                    data['store'] = None
        return data
