from apps.configuration.models import Settings
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db.models.query import QuerySet
from django.template.exceptions import TemplateDoesNotExist
from django.template.loader import render_to_string
import time

from .models import Emails


class Mailer:
    """
    Вспомогательный класс для отправки почты

    sender - email с которого происходит отправка
    recipients - получатели письма
    template_name - путь до папки с шаблонами сообщений
        папка должна содержать следующие файлы
        subject.txt - тема письма
        message.txt - текстовый шаблон
        message.html - шаблон html

        Текстовое содержание письма нужно для получаетелей, не имеющих
        клиента способного отображать html.
        (хотя таких почти не существует, кроме Феди со своим пейджером)

    context_data - словарь контекста, передаваемый в шаблон
    attachments - вложения письма
    """

    sender = None
    recipients = None
    template_name = None
    context_data = None
    attachments = None

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            if not hasattr(self, key):
                raise TypeError(u'%s() received an invalid keyword %r' % (
                    type(self).__name__, key))
            setattr(self, key, value)

    def get_sender(self):
        sender = self.sender or settings.DEFAULT_FROM_EMAIL
        site_name = Settings.get_settings().name
        if site_name:
            sender = f'{site_name} <{sender}>'
        return sender

    def get_recipients(self):
        if isinstance(self.recipients, (list, tuple)):
            return self.recipients
        if isinstance(self.recipients, QuerySet):
            return self.recipients._clone()
        return ()

    def get_template_name(self):
        return self.template_name

    def get_subject_template_name(self):
        return self.get_template_name() + '/subject.txt'

    def get_text_message_template_name(self):
        return self.get_template_name() + '/message.txt'

    def get_html_message_template_name(self):
        print("Template name", self.get_template_name())
        return self.get_template_name() + '/message.html'

    def get_subject(self, context=None):
        subject = render_to_string(
            template_name=self.get_subject_template_name(),
            context=context,
        )
        return ''.join(subject.splitlines())

    def get_text_message(self, context=None):
        try:
            return render_to_string(
                template_name=self.get_text_message_template_name(),
                context=context,
            )
        except TemplateDoesNotExist:
            return ''

    def get_html_message(self, context=None):
        try:

            print("Template name", self.get_html_message_template_name())

            message = render_to_string(
                template_name=self.get_html_message_template_name(),
                context=context,
            )
        except TemplateDoesNotExist:
            message = None
        return message

    def get_context_data(self, **kwargs):
        kwargs.update(self.context_data or {})
        return kwargs

    def get_message(self, subject, text, html, from_email, to):
        message = EmailMultiAlternatives(subject, text, from_email, to)
        if html:
            message.attach_alternative(html, 'text/html')
        if isinstance(self.attachments, (list, tuple)):
            for item in self.attachments:
                if isinstance(item, basestring):
                    message.attach_file(item)
                elif isinstance(item, (list, tuple)):
                    message.attach(*item)
                else:
                    raise ValueError('%r: is not tuple or string' % item)
        return message

    def get_connection(self):
        return get_connection(fail_silently=self.fail_silently)

    @classmethod
    def render_message(cls, **kwargs):
        mailer = cls(**kwargs)
        from_email = mailer.get_sender()
        context = mailer.get_context_data()
        subject = mailer.get_subject(context)
        text = mailer.get_text_message(context)
        html = mailer.get_html_message(context)
        to = mailer.get_recipients()

        Emails(from_mail=from_email, recipients=to, subject=subject, message=html, text=text).save()

        """
            09.12.2021
            Не отправлялось письмо после оформления заказа
            почему то небыло отправки после сохранения в БД
            возможно в этом был смысл?
        """
        cls.send(from_email=from_email, to=to, subject=subject, html=html, text=text)

    @classmethod
    def send(cls, subject, html, to, text=None, from_email=None, **kwargs):
        mailer = cls(**kwargs)
        from_email = mailer.get_sender()
        message = mailer.get_message(
            subject=subject,
            text=text,
            html=html,
            from_email=from_email,
            to=to)
        try:
            send = message.send()
            print(f'=====SEND MESSAGE SUCCESS {send}')
            return send
        except Exception as error:
            print('=========Ошибка', error)
            return int(settings.DEBUG)
