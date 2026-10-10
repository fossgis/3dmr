from django.core.cache import cache
from .models import Model, Category

def search_filters(request):
    data = cache.get('search_filters')
    if data is None:
        tags = set()
        for t in Model.objects.filter(latest=True).values_list('tags', flat=True):
            for k, v in (t or {}).items():
                tags.add('{}={}'.format(k, v))
        data = {
            'all_categories': sorted(Category.objects.values_list('name', flat=True)),
            'all_tags': sorted(tags),
        }
        cache.set('search_filters', data, 300)
    return data
