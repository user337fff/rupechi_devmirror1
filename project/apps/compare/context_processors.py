from .models import get_compare


def compare(request):
    compare = get_compare(request)
    return {'compare': compare}
