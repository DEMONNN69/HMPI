# calculations/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'computed-indices', views.ComputedIndexViewSet)
router.register(r'calculation-batches', views.CalculationBatchViewSet)

urlpatterns = [
    path('api/v1/', include(router.urls)),
]