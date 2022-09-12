from apps.commons.mixins import ContextPageMixin
from apps.feedback.mailer import Mailer
from apps.feedback.models import Mail
from django import forms
from django.contrib.auth import login, authenticate, logout as django_logout
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import PasswordChangeView, PasswordResetConfirmView
from django.contrib.auth.views import PasswordResetView
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls import reverse_lazy, reverse
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views import generic, View
from django.http import Http404
from apps.domains.middleware import get_request

from .forms import SignupForm, AuthenticationForm
from .models import Account
from .tokens import account_activation_token
from ..commons.mixins import ContextPageMixin, AjaxableResponseMixin, CustomListMixin
from ..feedback.models import Mail
from ..pages.models import Page


class UserPasswordChangeView(ContextPageMixin, PasswordChangeView):
    success_url = '/users/password/change/'
    template_name = 'users/personal/change_password.html'
    page = Page.TemplateChoice.CHANGE_PASSWORD


class SignupView(generic.FormView):
    """ Регистрация нового пользователя  """
    form_class = SignupForm
    success_url = reverse_lazy("user-update")
    template_name = "users/signup.html"
    user = None

    def send_email_confirm(self, email, password=''):
        if self.user is not None:
            current_site = get_current_site(self.request)
            mail_subject = 'Активация учетной записи'
            message = render_to_string('users/mail/user_confirm.html', {
                'user': self.user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(self.user.pk)),
                'token': account_activation_token.make_token(self.user),
                'request': self.request,
                'password': password,
            })
            email = EmailMessage(
                mail_subject, message, to=[email]
            )
            email.send()

    @transaction.atomic
    def form_valid(self, form):
        password = Account.objects.make_random_password()
        self.user = form.save(commit=False)
        self.user.is_active = True
        self.user.set_password(password)
        self.user.save()
        email = form.cleaned_data.get('email')
        login(self.request, self.user, backend='django.contrib.auth.backends.ModelBackend')
        data = {
            "success": True,
            "redirect": self.get_success_url()
        }
        self.send_email_confirm(email, password)
        mail = Mail.objects.filter(type=Mail.TypeChoice.REGISTER, domains__exact=self.request.domain).first()
        emails = list(mail.recipients.values_list('email', flat=True))
        context = {
            'mail': mail,
            'request': self.request,
            'user': self.user,
        }
        Mailer.render_message(recipients=emails, template_name=f'feedback/register', context_data=context)
        return JsonResponse(data)

    def form_invalid(self, form):
        return JsonResponse(
            {
                "success": False,
                "errors": form.errors
            }
        )


class UserPasswordResetView(PasswordResetView):
    email_template_name = 'registration/pass_reset_email.html'

    def form_valid(self, form):
        super(UserPasswordResetView, self).form_valid(form)
        return JsonResponse({'success': True, 'message': 'Информация отправлена вам на почту'})


class ActivateUserView(generic.View):
    """ Активация учетной записи пользователя  """

    def get(self, request, *args, **kwargs):
        uidb64 = kwargs.get('uidb64')
        token = kwargs.get('token')
        try:
            uid = force_text(urlsafe_base64_decode(uidb64))
            user = Account.objects.get(pk=uid)
        except(TypeError, ValueError, OverflowError, Account.DoesNotExist):
            user = None
        if (user is not None and
                account_activation_token.check_token(user, token)):
            user.is_active = True
            user.save()
            login(request, user)
            return redirect('/')
        return HttpResponse('Activation link is invalid!')


class Login(generic.FormView):
    """ Авторизация """
    form_class = AuthenticationForm
    success_url = "/"
    template_name = "users/signup.html"

    def form_valid(self, form):
        email = form.cleaned_data["email"]
        password = form.cleaned_data["password"]
        user = authenticate(email=email, password=password)
        if user is not None and user.is_active:
            login(self.request, user)
            data = {"success": True, "redirect": self.get_success_url()}
            return JsonResponse(data)
        else:
            return JsonResponse(
                {
                    "fields": {
                        "email": "Неверный логин или пароль",
                        "password": "Неверный логин или пароль",
                    },
                    "success": False,
                }
            )

    def form_invalid(self, form):
        return JsonResponse({"success": False, "fields": form.errors})


def logout(request):
    """ Выход из личного кабинета """
    django_logout(request)
    return redirect("/")


class UserUpdateView(LoginRequiredMixin, AjaxableResponseMixin, generic.UpdateView, ContextPageMixin):
    model = Account
    template_name = "users/personal/data.html"
    success_url = reverse_lazy('user-update')
    fields = ("name", "phone", "email_new")
    page = Page.TemplateChoice.LK
    message_success = 'Данные успешно обновлены'
    object = None

    def get_initial(self):
        initial = super(UserUpdateView, self).get_initial()
        for field in self.fields:
            if field == 'email_new':
                initial[field] = getattr(self.request.user, 'email', '')
            else:
                initial[field] = getattr(self.request.user, field, '')
        return initial

    def get_object(self, queryset=None):
        return self.request.user

    def send_email_confirm(self, email):
        if self.object:
            current_site = get_current_site(self.request)
            mail_subject = 'Подтверждение смены адреса электронной почты'
            message = render_to_string('users/mail/new_email_confirm.html', {
                'user': self.object,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(self.object.pk)),
                'token': account_activation_token.make_token(self.object),
                'request': self.request,
            })
            email = EmailMessage(
                mail_subject, message, to=[email]
            )
            email.send()

    def form_valid(self, form):
        if 'email_new' in form.changed_data:
            email_new = form.cleaned_data['email_new']
            # проверяем нет ли другого аккаунта с такой же почтой
            try:
                email_exist = Account.objects.filter(email=email_new).exists()
            except Account.DoesNotExist:
                email_exist = False
            if email_exist:
                form._errors["email_exist"] = form.error_class(
                    ["Данный email уже зарегистрирован"])
                del form.cleaned_data["email_exist"]
                return self.form_invalid(form)
            self.send_email_confirm(email_new)
        # TODO: Сохранение формы
        return super().form_valid(form)


class ConfirmNewEmailView(generic.View):
    """ Активация учетной записи пользователя  """

    def get(self, request, *args, **kwargs):
        uidb64 = kwargs.get('uidb64')
        token = kwargs.get('token')
        try:
            uid = force_text(urlsafe_base64_decode(uidb64))
            user = Account.objects.get(pk=uid)
        except(TypeError, ValueError, OverflowError, Account.DoesNotExist):
            user = None
        if (user is not None and
                account_activation_token.check_token(user, token)):
            user.email = user.email_new
            user.email_new = ''
            user.save()
            return redirect(reverse('user-update'))
        return HttpResponse('Confirm email link is invalid!')


class UserOrdersTemplateView(CustomListMixin, ContextPageMixin, generic.TemplateView):
    template_name = 'users/personal/orders.html'
    page = Page.TemplateChoice.ORDERS

    def get_items(self):
        return []


class ResetForm(forms.Form):
    new_password1 = forms.CharField(label='Новый пароль', widget=forms.PasswordInput())
    new_password2 = forms.CharField(label='Повторите новый пароль', widget=forms.PasswordInput())

    def clean(self):
        data = self.cleaned_data
        password = data.get('new_password1')
        if password and password != data.get('new_password2'):
            raise forms.ValidationError({"new_password2": 'Пароль не совпадает'})

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        password = self.cleaned_data["new_password1"]
        self.user.set_password(password)
        if commit:
            self.user.save()
        return self.user


class UserSetNewPassword(ContextPageMixin, PasswordResetConfirmView):
    template_name = 'registration/pass_reset_confirm.html'
    form_class = ResetForm
    page = Page.TemplateChoice.RESET

    def form_valid(self, form):
        super(UserSetNewPassword, self).form_valid(form)
        return JsonResponse({'success': True, 'message': 'Пароль обновлен'})

    def form_invalid(self, form):
        super(UserSetNewPassword, self).form_invalid(form)
        return JsonResponse({'success': False, 'errors': form.errors})

class UserAuthSocialRedirect(View):

    MAIN_DOMAIN = "https://www.devmirror1.srv-rupechi-test1.place-start.ru/"

    VK = "vk"
    TYPES = (VK)

    REQUEST_FROM_DOMAIN = "1"
    REDIRECT_ON_MAIN_DOMAIN = "2"
    SUCCESSFULL_AUTH = "3"
    ACTIONS = (REQUEST_FROM_DOMAIN, REDIRECT_ON_MAIN_DOMAIN, SUCCESSFULL_AUTH)

    def get(self, request, *args, **kwargs):

        selected_type = request.GET.get("type", "")
        action = request.GET.get("action", "")
        print("Absolute uri", request.build_absolute_uri())
        print("current scheme", request._current_scheme_host)
        print(request.scheme, request.get_host())

        if(not action in self.ACTIONS):
            raise Http404

        if(action == self.REQUEST_FROM_DOMAIN):
            redirect_basic = reverse("social_auth_redirect")
            if(not selected_type in self.TYPES):
                raise Http404

            redirect_response = redirect(self.MAIN_DOMAIN + redirect_basic + "?action=2&type=" + selected_type)

            redirect_response.set_cookie("domain_redirect", str("www.devmirror1.srv-rupechi-test1.place-start.ru"))
            redirect_response.set_cookie("domain_redirect", str(get_request().domain.domain))

            return redirect_response

        elif(action == self.REDIRECT_ON_MAIN_DOMAIN):
            if(not selected_type in self.TYPES):
                raise Http404

            if(selected_type == self.VK):
                return redirect(self.MAIN_DOMAIN + "/login/vk-oauth2/")

            elif(selected_type == self.YANDEX):
                return redirect(self.MAIN_DOMAIN + "/login/yandex-oauth2/")

        elif(action == self.SUCCESSFULL_AUTH):
            domain = request.COOKIES.get("domain_redirect", self.MAIN_DOMAIN)

            print(domain, "https://" + domain)

            redirect_response = redirect("https://" + domain)

            redirect_response.delete_cookie("domain_redirect")

            return redirect_response

        raise Http404