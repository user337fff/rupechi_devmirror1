from django.template.loader import get_template
from django.views.generic import FormView, TemplateView

from apps.commons.mixins import AjaxableResponseMixin, CustomListMixin, ContextPageMixin
from .forms import WishlistProductForm
from .models import get_wishlist
from ..pages.models import Page


class WishlistTemplateView(ContextPageMixin, CustomListMixin, TemplateView):
    template_name = 'wishlist/wishlist.html'
    page = Page.TemplateChoice.WISHLIST
    template_card_name = 'catalog/product_card.html'
    paginate_by = 8

    def get_items(self):
        return get_wishlist(self.request).items()

    def render(self, item):
        return get_template(self.template_card_name).render({
            'product': item.product,
            'actions': 'trash',
        })


class ToggleWishlistFormView(AjaxableResponseMixin, FormView):
    """
    Добавление товара в корзину
    """
    form_class = WishlistProductForm
    message_success = "Элемент сравнения успешно изменен"

    def form_valid(self, form):
        self.wishlist = get_wishlist(self.request)
        self.wishlist.toggle(**form.cleaned_data)
        self.extra_response_data = {'count': self.wishlist.count}
        return super().form_valid(form)
