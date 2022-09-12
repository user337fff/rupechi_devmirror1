from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template.exceptions import TemplateDoesNotExist
from django.views.generic import FormView

from .finder import template_list, TemplateFinder
from .forms import TemplateForm, TEMPLATE_PATH_CHOICES


class TemplateEditFormView(UserPassesTestMixin, FormView):
    template_name = 'template_editor/admin/template_edit.html'
    form_class = TemplateForm

    def test_func(self):
        """
        Доступ только для суперпользователей
        """
        return self.request.user.is_superuser

    def form_valid(self, form):
        template_name = form.cleaned_data['template']
        template_content = form.cleaned_data['template_content']

        template_path = TemplateFinder.search_by_name(
            template_name, template_list)
        if template_path is not None:
            TemplateFinder.set_template_content(
                template_path, template_content)
            messages.add_message(
                self.request,
                messages.SUCCESS,
                f'Шаблон "{template_name}" успешно изменен')

        return HttpResponseRedirect(f'.?template={template_name}')

    def get_initial(self):
        """Начальные значения формы"""
        initial = super().get_initial()

        # получаем имя шаблона из гет-параметра,
        # если не задан, то берем первый из чойсеса
        template_name = self.request.GET.get('template', TEMPLATE_PATH_CHOICES[0][0])
        template_path = TemplateFinder.search_by_name(
            template_name, template_list)
        if template_path is not None:
            with open(template_path, 'r') as file:
                return {
                    'template': template_name,
                    'template_content': file.read()
                }
        return initial


@user_passes_test(lambda user: user.is_superuser)
def get_template_content(request):
    """Получение содержимого по имени шаблона"""
    template_name = request.POST.get('template')
    content = None
    if template_name is not None:
        content = TemplateFinder.get_template_content_by_name(
            template_name, template_list)
    if content is None:
        print('*** HTTP EXCEPT 404', 'apps/template_editor.py 66')
        raise Http404
    return HttpResponse(content)
