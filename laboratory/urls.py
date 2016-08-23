from django.conf.urls import url
from django.urls import reverse_lazy

from laboratory.views import index
from django.contrib.auth import views as auth_views

urlpatterns = [
    url(r'^$', index, name='index'),
    url(r'^login$', auth_views.login, {'template_name': 'laboratory/login.html'}, name='login'),
    url(r'^logout$', auth_views.logout, {'next_page': reverse_lazy('laboratory:index')}, name='logout')
]