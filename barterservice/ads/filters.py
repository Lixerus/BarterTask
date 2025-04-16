import django_filters
from .models import Ad


class AdFilter(django_filters.FilterSet):
    category = django_filters.CharFilter(field_name='category')
    condition = django_filters.CharFilter(field_name='condition')

    class Meta:
        model = Ad
        fields = ['category', 'condition']