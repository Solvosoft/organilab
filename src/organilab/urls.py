"""organilab URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  re_path(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  re_path(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  re_path(r'^blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import re_path, path, include

from laboratory import urls as laboratory_urls

from djreservation import urls as djreservation_urls
from academic.urls import urlpatterns as academic_urls
from authentication.urls import urlpatterns as auth_urls
from django.conf import settings

from laboratory.reactive import ReactiveMolecularFormulaAPIView
from msds.urls import urlpatterns as msds_urls
from api.urls import urlpatterns as api_urls
from django.views.generic.base import RedirectView
from django.urls.base import reverse_lazy
from djgentelella.urls import urlpatterns as urls_djgentelela

from sga import urls as sga_urls
from risk_management import urls as risk_urls
from sga.views import index_organilab, donate, donate_success

from reservations_management.urls import urlpatterns as reservation_management_urls
from reservations_management.api.urls import urlpatterns as reservations_management_api_urlpatterns

urlpatterns = urls_djgentelela + auth_urls + [
    path('derb/', include('derb.urls')),
    path('index/', include('presentation.urls')),
    path('perms/', include('auth_and_perms.urls', namespace='auth_and_perms')),
    re_path(r'^$', index_organilab, name='index'),
    re_path(r'^', include((laboratory_urls,'laboratory'), namespace='laboratory')),
    re_path(r'^', include((api_urls,'api'), namespace='api')),
    re_path(r'msds/', include((msds_urls, 'msds'), namespace='msds')),
    re_path(r'^weblog/', include('djgentelella.blog.urls')),
    re_path(r'sga/', include((sga_urls, 'sga'), namespace='sga')),
    re_path(r'risk/', include((risk_urls, 'riskmanagemen'), namespace='riskmanagement')),
    re_path(r'^api/reactive/name/', ReactiveMolecularFormulaAPIView.as_view(), name="api_molecularname"),
    re_path(r'^markitup/', include('markitup.urls')),
    re_path(r'^admin/', admin.site.urls),
    re_path(r'^donate$', donate, name='donate'),
    re_path(r'^donate_success$', donate_success, name='donate_success'),
]

paypal_urls = [
    re_path(r'^paypal/', include('paypal.standard.ipn.urls')),
]

urlpatterns += paypal_urls
urlpatterns += djreservation_urls.urlpatterns
urlpatterns += academic_urls
urlpatterns += reservation_management_urls
urlpatterns += reservations_management_api_urlpatterns

if settings.DEBUG:
    from django.conf.urls.static import static
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

