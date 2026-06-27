from django.contrib.auth.models import User
from django_filters import FilterSet


class UserFilter(FilterSet):
    class Meta:
        model = User
        fields = {
            "first_name": ["icontains"],
            "last_name": ["icontains"],
            "username": ["icontains"],
            "email": ["icontains"],
        }
