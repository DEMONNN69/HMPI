# calculations/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .map_views import get_map_data

router = DefaultRouter()
router.register(r'computed-indices', views.ComputedIndexViewSet)
router.register(r'calculation-batches', views.CalculationBatchViewSet)

urlpatterns = [
    path('api/v1/', include(router.urls)),
    path('api/v1/map-data/', get_map_data, name='map-data'),
]