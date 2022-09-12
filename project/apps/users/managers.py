from django.contrib.auth.base_user import BaseUserManager
from django.utils.translation import ugettext_lazy as _
from apps.feedback.models import Mail
from django.core.mail import EmailMessage
from apps.domains.middleware import get_request
from django.template.loader import render_to_string


class AccountManager(BaseUserManager):
    """
    Custom user model manager where email is the unique identifiers
    for authentication instead of usernames.
    """

    def create_user(self, email, password='', **extra_fields):
        """
        Create and save a User with the given email and password.
        """
        # при авторизации с фейсбука может не придти почта
        if email:
            email = self.normalize_email(email)
            extra_fields['email'] = email
        password = password or self.model.objects.make_random_password()
        user = self.model(**extra_fields)
        user.set_password(password)
        user.save()
        domain = get_request().domain
        # mail = Mail.objects.filter(type=Mail.TypeChoice.REGISTER, domains__exact=domain).first()
        # if mail:
        #     mail_subject = 'Регистрация нового пользователя'
        #     message = render_to_string('feedback/new_user.html', {
        #         'user': user,
        #     })
        #     EmailMessage(
        #         mail_subject, message, to=list(mail.recipients.values_list('email', flat=True))
        #     ).send()
        return user

    def create_superuser(self, email, password, **extra_fields):
        """
        Create and save a SuperUser with the given email and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self.create_user(email, password, **extra_fields)
