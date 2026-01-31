"""
URL Configuration for Core App.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    ChildProfileViewSet,
    ParentalRuleViewSet,
    RuleViolationViewSet,
    NetworkDeviceViewSet,
    NetworkScanLogViewSet,
    PrivacyCheckView,
    PrivacyCheckListView,
)
from .views_auth import (
    RegisterView,
    LoginView,
    SocialLoginGoogleView,
    SocialLoginAppleView,
    MeView,
)

# Create router for ViewSets
router = DefaultRouter()
router.register(r'children', ChildProfileViewSet, basename='children')
router.register(r'parental/rules', ParentalRuleViewSet, basename='parental-rules')
router.register(r'parental/violations', RuleViolationViewSet, basename='parental-violations')
router.register(r'network/devices', NetworkDeviceViewSet, basename='network-devices')
router.register(r'network/scans', NetworkScanLogViewSet, basename='network-scans')

urlpatterns = [
    # Authentication endpoints
    path('auth/register/', RegisterView.as_view(), name='auth-register'),
    path('auth/login/', LoginView.as_view(), name='auth-login'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='auth-token-refresh'),
    path('auth/social/google/', SocialLoginGoogleView.as_view(), name='auth-social-google'),
    path('auth/social/apple/', SocialLoginAppleView.as_view(), name='auth-social-apple'),
    path('auth/me/', MeView.as_view(), name='auth-me'),

    # Privacy endpoints
    path('privacy/check/', PrivacyCheckView.as_view(), name='privacy-check'),
    path('privacy/checks/', PrivacyCheckListView.as_view(), name='privacy-checks'),

    # Include router URLs
    path('', include(router.urls)),
]
