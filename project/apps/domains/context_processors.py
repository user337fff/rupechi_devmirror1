from apps.domains.models import Domain


def context_domains(request):
    return {'domains': Domain.objects.all()}
