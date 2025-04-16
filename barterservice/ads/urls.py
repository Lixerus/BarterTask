from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AdViewSet, ExchangeProposalViewSet

router = DefaultRouter()

router.register(r'ads', AdViewSet)
router.register(r'proposals', ExchangeProposalViewSet, basename='proposal')

urlpatterns = [
    path('', include(router.urls)),
]

app_name = 'exchange_api'