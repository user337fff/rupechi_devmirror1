from django.apps import apps
from django.http import JsonResponse
from django.views.generic.base import View
from django.views.generic.edit import ProcessFormView

from apps.domains.middleware import request_object
from apps.domains.models import Domain
from django.http import Http404

class ChangeDomain(ProcessFormView, View):

    def post(self, *args, **kwargs):
        domain = self.request.POST.get('domain')
        app = self.request.POST.get('app')
        model = self.request.POST.get('model')
        id = self.request.POST.get('id')
        request_object.request.domain = Domain.objects.filter(domain=domain).first()
        model = apps.get_model(app, model)
        obj = model.objects.filter(domain__exact=domain, id=id).first()
        url = domain
        if obj:
            url += obj.get_absolute_url()
        return JsonResponse({'url': url})
    
    def get(self, *args, **kwargs):
        raise Http404
