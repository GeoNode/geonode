from django.core.cache import cache

from .models import GeoNodeThemeCustomization, THEME_CACHE_KEY


def custom_theme(request):
    theme = cache.get(THEME_CACHE_KEY)
    if theme is None:
        try:
            theme = GeoNodeThemeCustomization.objects.prefetch_related('partners').get(is_enabled=True)
            slides = theme.jumbotron_slide_show.filter(is_enabled=True)
        except Exception:
            theme = {}
            slides = []
        cache.set(THEME_CACHE_KEY, theme)
    else:
        try:
            slides = theme.jumbotron_slide_show.filter(is_enabled=True)
        except Exception:
            slides = []
    return {'custom_theme': theme, 'slides': slides}
