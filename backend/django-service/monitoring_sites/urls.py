# monitoring_sites/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'monitoring-sites', views.MonitoringSiteViewSet)

urlpatterns = [
    path('api/v1/', include(router.urls)),
]