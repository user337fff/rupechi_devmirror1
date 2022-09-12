from .models import MenuItem
from ..pages.models import Page


def context_nav(request):
    response = {
        'header_items': MenuItem.get_header(),
        'footer_items': MenuItem.get_footer(),
        'catalog_items': MenuItem.get_catalog()
    }

    pages = {
        Page.TemplateChoice.PERSONAL: 'personal_page',
        Page.TemplateChoice.PUBLIC: 'public_page',
        Page.TemplateChoice.PRIVACY: 'privacy_page',
        Page.TemplateChoice.SITEMAP: 'sitemap_page',
        Page.TemplateChoice.CALCULATOR: 'calc_page',
    }

    qs = Page.objects.activated(template__in=pages.keys())

    for page in qs.iterator():
        response.update({pages.get(page.template): page})
        
    return response
