from django import template
from django.conf import settings
from django.template.base import Node

register = template.Library()


@register.simple_tag
def get_only_name(value):
    only_name_set = []
    for item in value:
        if item.name:
            only_name_set.append(item)
    return only_name_set


@register.inclusion_tag('administration/menu.html', takes_context=True)
def admin_nav(context):
    navigation = []
    other = []
    try:
        if 'available_apps' in context:
            app_list = list(context['available_apps'])
            for available_apps in settings.ADMIN_NAVIGATION:
                # Приложение в разделе
                try:
                    apps = []
                    for app in available_apps['apps']:

                        for item in app_list:
                            models = []
                            if item['name'] == app[0] or item['app_label'] == app[0]:
                                model_list = list(item['models'])
                                for model_name in app[1]:
                                    for model_def in model_list:
                                        if model_def['name'] == model_name:
                                            models.append(model_def)
                                            model_list.remove(model_def)
                                            break
                                models[len(models):] = model_list
                                apps.append({
                                    'name': item['name'],
                                    'app_label': item['app_label'],
                                    'app_url': item['app_url'],
                                    'models': models
                                })
                                app_list.remove(item)
                    navigation.append({
                        'name': available_apps['name'],
                        'apps': apps
                    })
                # Вывод сразу приложений
                except:
                    for item in app_list:
                        models = []
                        if item['name'] == available_apps[0] or item['app_label'] == available_apps[0]:
                            model_list = list(item['models'])
                            for model_name in available_apps[1]:
                                for model_def in model_list:
                                    if model_def['name'] == model_name:
                                        models.append(model_def)
                                        model_list.remove(model_def)
                                        break
                            models[len(models):] = model_list
                            navigation.append({
                                'name': item['name'],
                                'app_label': item['app_label'],
                                'app_url': item['app_url'],
                                'models': models
                            })
                            app_list.remove(item)

            other = app_list
        return locals()
    except:
        return ''


class AppOrderNode(Node):
    def render(self, context):
        if 'app_list' in context:
            app_list = list(context['app_list'])
            ordered = []
            for app in settings.ADMIN_REORDER:
                app_name, app_models = app[0], app[1]
                for app_def in app_list:
                    if app_def['name'] == app_name:
                        model_list = list(app_def['models'])
                        models = []
                        for model_name in app_models:
                            for model_def in model_list:
                                if model_def['name'] == model_name:
                                    models.append(model_def)
                                    model_list.remove(model_def)
                                    break
                        models[len(models):] = model_list
                        ordered.append({
                            'app_label': app_def['app_label'],
                            'app_url': app_def['app_url'],
                            'models': models,
                            'name': app_def['name']
                        })
                        app_list.remove(app_def)
                        break
            ordered[len(ordered):] = app_list
            context['app_list'] = ordered
        return ''


@register.tag()
def app_order(parser, token):
    return AppOrderNode()
