import json

from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from django.utils.decorators import method_decorator
from django.http import JsonResponse

from .models import KomtetRequest


class KomtetSuccsessView(View):
    """Обработчик колбека комтет-кассы о успешной операции"""
    STATUS = KomtetRequest.SUCCESS

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request):
        try:
            body = request.body.decode('utf-8')
            data = json.loads(body)
        except json.decoder.JSONDecodeError:
            return JsonResponse({"success": False,
                                 "error": "Invalid data format"}, status=200)

        order_id = data.get('external_id', 0)
        komtet = get_object_or_404(KomtetRequest, order_id=order_id)
        komtet.status = self.STATUS
        komtet.response = data
        komtet.save()
        return JsonResponse({"success": True}, status=200)


class KomtetFailureView(View):
    STATUS = KomtetRequest.ERROR
