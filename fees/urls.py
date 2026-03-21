"""
Fee Management URL Configuration

Routes for fee categories, structures, discounts, student fees, payments, and reports.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    FeeCategoryViewSet,
    FeeStructureViewSet,
    FeeDiscountViewSet,
    StudentFeeViewSet,
    FeePaymentViewSet,
    FeeReportsViewSet,
)

router = DefaultRouter()
router.register(r'categories', FeeCategoryViewSet, basename='fee-category')
router.register(r'structures', FeeStructureViewSet, basename='fee-structure')
router.register(r'discounts', FeeDiscountViewSet, basename='fee-discount')
router.register(r'student-fees', StudentFeeViewSet, basename='student-fee')
router.register(r'payments', FeePaymentViewSet, basename='fee-payment')
router.register(r'reports', FeeReportsViewSet, basename='fee-report')

urlpatterns = [
    path('', include(router.urls)),
]
