CITY_SHORTCODE = '||city||'
CITY_SHORTCODE_LOCT = '||city1||'


def replace_city(value, domain):
    """
    Замена шорткода города на название города в нужной форме
    """
    name, name_loct = domain.name, domain.name_loct
    if CITY_SHORTCODE in value or CITY_SHORTCODE_LOCT in value:
        value = value.replace(CITY_SHORTCODE, name)
        value = value.replace(CITY_SHORTCODE_LOCT, name_loct)
    return value