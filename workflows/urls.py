"""
Workflows URL Configuration

API endpoints for request types, workflows, requests, approvals, and clearances.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RequestTypeViewSet,
    ApprovalWorkflowViewSet,
    ClearanceTypeViewSet,
    RequestViewSet,
)

router = DefaultRouter()
router.register(r'request-types', RequestTypeViewSet, basename='request-type')
router.register(r'workflows', ApprovalWorkflowViewSet, basename='workflow')
router.register(r'clearance-types', ClearanceTypeViewSet, basename='clearance-type')
router.register(r'requests', RequestViewSet, basename='request')

urlpatterns = [
    path('', include(router.urls)),
]
