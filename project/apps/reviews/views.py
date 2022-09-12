from django import forms
from django.http import JsonResponse
from django.views.generic.base import View
from django.views.generic.edit import ProcessFormView

from apps.reviews.models import Review


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        exclude = ['date_created', 'sort']

    def clean_is_active(self):
        return False


class SetReview(ProcessFormView, View):

    def post(self, request, *args, **kwargs):
        form = ReviewForm(request.POST)
        response = {}
        if form.is_valid():
            form.save()
            response['success'] = 'Комментарий добавлен'
        else:
            response['errors'] = form.errors
        print(response)
        return JsonResponse(response)
