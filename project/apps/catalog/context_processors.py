from ..stores.models import Store


def context_catalog(request):
    q = request.GET.get('q')
    shops = Store.objects.filter(domain=request.domain, is_footer=True)
    return {'q': q, 'shops': shops}
