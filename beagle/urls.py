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
from beagle import __version__
from core.views import BeagleTokenObtainPairView, BeagleTokenRefreshView, BeagleTokenVerifyView, UserRequestViewSet
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from rest_framework import routers


schema_view = get_schema_view(
   openapi.Info(
      title="Beagle API",
      default_version=__version__
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)


router = routers.DefaultRouter()
router.register('register', UserRequestViewSet)


urlpatterns = [
    url(r'^$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    url(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('', include(router.urls)),
    path('v0/fs/', include('file_system.urls')),
    path('v0/run/', include('runner.urls')),
    path('v0/etl/', include('beagle_etl.urls')),
    path('v0/notifier/', include('notifier.urls')),
    path('admin/', admin.site.urls),
    path('api-token-auth/', BeagleTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api-token-refresh/', BeagleTokenRefreshView.as_view(), name='token_refresh'),
    path('api-token-verify/', BeagleTokenVerifyView.as_view(), name='token_verify')
]
