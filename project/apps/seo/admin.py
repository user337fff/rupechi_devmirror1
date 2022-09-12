class SeoAdminMixin(object):
    seo_fields = [
        'meta_title',
        'meta_description',
        'meta_keywords',
    ]

    seo_fields_full = ['seo_img', 'seo_text'] + seo_fields
