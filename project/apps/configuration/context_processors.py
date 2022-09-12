from .models import Settings


def context_settings(request):
    v = 2
    return {'settings': Settings.load(), 'domain': request.domain, 'v': v}
