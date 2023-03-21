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

from django.conf import settings
from django.contrib import admin
from django.urls import re_path, path, include, reverse_lazy
from django.views.generic import RedirectView
from djgentelella.urls import urlpatterns as urls_djgentelela
from djreservation import urls as djreservation_urls

from academic.urls import urlpatterns as academic_urls
from api.urls import urlpatterns as api_urls
from auth_and_perms.views import media_access
from authentication.urls import urlpatterns as auth_urls
from laboratory import urls as laboratory_urls
from laboratory.reactive import ReactiveMolecularFormulaAPIView
from msds.urls import urlpatterns as msds_urls
from msds.urls import regulation_urlpath
from reservations_management.api.urls import urlpatterns as reservations_management_api_urlpatterns
from reservations_management.urls import urlpatterns as reservation_management_urls
from risk_management import urls as risk_urls
from sga import urls as sga_urls
from derb import urls as derb_urls
from django.views.i18n import JavaScriptCatalog

urlpatterns = urls_djgentelela + auth_urls + [
    path('', RedirectView.as_view(url=reverse_lazy('index')), name="home"),
    path('index/', include('presentation.urls')),
    path('perms/', include('auth_and_perms.urls', namespace='auth_and_perms')),
    path('', include((laboratory_urls,'laboratory'), namespace='laboratory')),
    path('', include((api_urls,'api'), namespace='api')),
    path('msds/<int:org_pk>/', include((msds_urls, 'msds'), namespace='msds')),
    path('weblog/', include('djgentelella.blog.urls')),
    path('sga/<int:org_pk>/', include((sga_urls, 'sga'), namespace='sga')),
    path('risk/<int:org_pk>/', include((risk_urls, 'riskmanagement'), namespace='riskmanagement')),
    path('derb/<int:org_pk>/', include((derb_urls, 'derb'), namespace='derb')),
    path('academic/<int:org_pk>/', include((academic_urls, 'academic'), namespace='academic')),
    path('reservations_management/<int:org_pk>/', include((reservation_management_urls, 'reservations_management'), namespace='reservations_management')),
    re_path(r'^api/reactive/name/', ReactiveMolecularFormulaAPIView.as_view(), name="api_molecularname"),
    re_path(r'^markitup/', include('markitup.urls')),
    path('admin/', admin.site.urls),
    path('async_notifications/', include('async_notifications.urls')),
    path("jsi18n/", JavaScriptCatalog.as_view(), name="javascript-catalog"),

]

paypal_urls = [
    re_path(r'^paypal/', include('paypal.standard.ipn.urls')),
]

urlpatterns += paypal_urls
urlpatterns += djreservation_urls.urlpatterns
urlpatterns += reservations_management_api_urlpatterns
urlpatterns += regulation_urlpath

if settings.DEBUG:
    from django.conf.urls.static import static
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    urlpatterns += [
        re_path('^media/(?P<path>.*)', media_access, name='media'),
    ]


