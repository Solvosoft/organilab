"""organilab URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
from laboratory import urls as laboratory_urls

from djreservation import urls as djreservation_urls
from academic.urls import urlpatterns as academic_urls
from ajax_select import urls as ajax_select_urls
from authentication.urls import urlpatterns as auth_urls
from django.conf import settings


urlpatterns = auth_urls + [
    url(r'^admin/', admin.site.urls),
    url(r'^', include(laboratory_urls, namespace='laboratory')),
    url(r'^ajax_select/', include(ajax_select_urls)),
]

if settings.FULL_APPS:
    from api import url as api_urls
    urlpatterns += [
        url(r'^api/', include(api_urls))
    ]
urlpatterns += djreservation_urls.urlpatterns
urlpatterns += academic_urls
