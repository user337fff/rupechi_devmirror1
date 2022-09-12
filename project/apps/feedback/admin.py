from django.contrib import admin

from apps.feedback.models import Mail, Recipient, Emails


@admin.register(Mail)
class MailAdmin(admin.ModelAdmin):
    list_display = ['type', 'cities']


@admin.register(Recipient)
class RecipientAdmin(admin.ModelAdmin):
    pass


admin.site.register(Emails)