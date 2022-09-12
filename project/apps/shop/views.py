import traceback
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.db import transaction
from django.http import JsonResponse, Http404, HttpResponseRedirect
from django.template.loader import get_template, render_to_string
from django.urls import reverse_lazy
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views.generic import FormView, RedirectView
from django.shortcuts import redirect
import json
import webbrowser


from django.views.generic import TemplateView
from .forms import OrderForm
from apps.users.tokens import account_activation_token
from ..commons.mixins import ContextPageMixin
from ..configuration.models import Settings
from ..pages.models import Page
from apps.feedback.models import Mail
from apps.feedback.mailer import Mailer
from apps.cart.models import Cart, CartItem, get_cart
from apps.cart.models.base import get_gefest
from apps.sber_acquiring.models import BankOrder
from apps.users.models import Account
from apps.shop.models import Order
from apps.catalog.models import Brand


class OrderCreateView(ContextPageMixin, FormView):
    """
    Оформление заказа
    """
    form_class = OrderForm
    template_name = 'shop/order.html'
    success_url = reverse_lazy('personal-orders')
    page = Page.TemplateChoice.ORDER

    def dispatch(self, request, *args, **kwargs):
        cart = get_cart(self.request)
        if not cart.exists() and not self.request.GET.get('success'):
            return redirect('index')
        return super(OrderCreateView, self).dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super(OrderCreateView, self).get_initial()
        if self.request.user.is_authenticated:
            initial['name'] = self.request.user.name
            initial['phone'] = self.request.user.phone
            initial['email'] = self.request.user.email
        return initial

    def form_invalid(self, form):
        return JsonResponse({'errors': form.errors, 'success': False})

    @staticmethod
    def get_success(**kwargs):
        settings = Settings.get_settings()
        template = 'shop/order_empty.html'
        return get_template(template).render({'settings': settings, **kwargs})

    def get_context_data(self, **kwargs):
        context = super(OrderCreateView, self).get_context_data(**kwargs)
        if self.request.GET.get('success'):
            order = self.request.GET.get('order')
            context['template'] = self.get_success(id=order)
        return context

    def get_receivers(self, cart):
        result_receivers = []
        cart_receivers = []
        
        #if self.request.domain.domain == 'spb.rupechi.ru':
        if get_gefest(get_cart(self.request)):
            result_receivers.append('tlcub@rupechi.ru')
        else:
            result_receivers.append('kubatura@rupechi.ru')

        #try:
        #    cart_items = CartItem.objects.filter(cart__id=cart.id)
        #    list_cart_receivers = [list(item.product.category.get_ancestors(include_self=True)) for item in cart_items]
        #    for cart_receiver in list_cart_receivers:
        #        cart_receivers.extend(cart_receiver)
        #    cart_receivers = [list(item.receivers.all()) for item in cart_receiver]
        #except:
        #    cart_receivers = [item.product.category.receivers.all() for item in cart.items()]

        #for cart_item in cart_receivers:
        #    result_receivers.extend(cart_item)

        return result_receivers

    @transaction.atomic
    def form_valid(self, form):
        # получение корзины
        cart = get_cart(self.request)
        cart_receivers = self.get_receivers(cart)
        user = self.request.user
        if not user.is_authenticated:
            user, created = Account.objects.get_or_create(email=form.cleaned_data.get('email'),
                                                          defaults={
                                                              'name': form.cleaned_data.get('name'),
                                                              'phone': form.cleaned_data.get('phone')
                                                          })
            if created:
                password = Account.objects.make_random_password()
                user.set_password(password)
                current_site = get_current_site(self.request)
                mail_subject = 'Активация учетной записи'
                message = render_to_string('users/mail/user_confirm.html', {
                    'user': user,
                    'domain': current_site.domain,
                    'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                    'token': account_activation_token.make_token(user),
                    'request': self.request,
                    'password': password,
                })
                email = EmailMessage(
                    mail_subject, message, to=[form.cleaned_data.get('email')]
                )
                email.send()
                Account.auth(self.request, user)
                admin_mail = Mail.objects.filter(type=Mail.TypeChoice.REGISTER, domains__exact=self.request.domain).first()
                emails_admin = list(admin_mail.recipients.values_list('email', flat=True))
                mail_subject_admin = 'Регистрация нового пользователя'
                message_admin = render_to_string('feedback/register/message.html', {
                    'mail': email,
                    'request': self.request,
                    'user': user,
                })

                Mailer.send(
                    subject=mail_subject_admin,
                    html=message_admin, to=emails_admin
                )

            user.save()
            
        order = form.save(commit=False)
        order.user = user
        order.total = cart.total
        order.total_original = cart.total_without_discount
        order.city = self.request.domain.name
        order.domain = self.request.domain
        order.save()

        # добавление элементов заказа
        order.create_items(cart)
        order.send_notifications()
        order.send_admin_notifications(cart_receivers)

        # очистка корзины
        cart.clear()
        if str(form.cleaned_data.get('payment')) == 'На сайте картой Visa, Mastercard или Мир':
            try:
                order.status = Order.AWAITING
                order.save(update_fields=['status'])
                bank_order = BankOrder.register_order(order, self.request.domain.domain)
                return JsonResponse({
                    'success': True,
                    'redirect': True,
                    'redirect_url': bank_order.formUrl,
                    'template': self.get_success(id=order.id, pay_url=bank_order.formUrl, payment=True),
                    'order': {'id': order.id}
                })
            except Exception as e:
                print(f'=====DEBUG SBER PAYMENT ERROR {e}')
                raise
            
        return JsonResponse({
            'success': True,
            'redirect': False,
            'template': self.get_success(id=order.id, payment=False),
            'order': {
                'id': order.id,
            }
        })


class OrderPay(RedirectView):

    def get_redirect_url(self, *args, **kwargs):
        order = Order.objects.get(id=kwargs.get('order_id'))
        bank_order = BankOrder.register_order(order, self.request.domain.domain)
        try:
            print("Bank url", bank_order.formUrl)
            return bank_order.formUrl
        except:
            print(f'=====ERROR BANK ORDER {bank_order.__dict__}')
            return '/'


class NotPaymentView(TemplateView):
    template_name = "sber_acquiring/unsuccessful_payment.html"

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        try:
            context["id"] = Order.objects.get(bank_data__bank_id=self.request.GET.get("orderId")).pk
        except:
            traceback.print_exc()

        print(context)

        return context