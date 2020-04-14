"""beagle URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.conf.urls import url
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenVerifyView,
)
from core.views import BeagleTokenObtainPairView


from rest_framework_swagger.views import get_swagger_view


schema_view = get_swagger_view(title='Beagle API')


urlpatterns = [
    url(r'^$', schema_view),
    path('v0/fs/', include('file_system.urls')),
    path('v0/run/', include('runner.urls')),
    path('v0/etl/', include('beagle_etl.urls')),
    path('v0/notifier/', include('notifier.urls')),
    path('admin/', admin.site.urls),
    path('api-token-auth/', BeagleTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api-token-refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api-token-verify/', TokenVerifyView.as_view(), name='token_verify'),
]
