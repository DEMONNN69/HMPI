from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
# Import your ViewSet from the data_management app
from data_management.views import GroundWaterSampleViewSet

# Create a router instance
router = DefaultRouter()
# Register the ViewSet to handle the base route
# The basename is used to generate the API link name
# FIX: Change the URL prefix from the default 'ground-water-samples' 
# to ensure it generates the correct slug matching your frontend request.
router.register(r'ground-water-samples', GroundWaterSampleViewSet, basename='ground-water-samples')

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Include the DRF router URLs under the 'api/v1/' prefix
    path('api/v1/', include(router.urls)),
]
