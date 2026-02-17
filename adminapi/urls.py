from django.urls import include, path
from TermdAndPrivacy.views import TermsAPIView,PrivacyAPIView
from truck.views import TruckListCreateView, TruckDetailAPIView,PriceManagementListCreateAPIView,PriceManagementDetailAPIView,MoversManagementListCreateAPIView,MoversManagementDetailAPIView

from notifications.views import NotificationListAPIView

from booking.views import BookingAdminUpdateView,BookingAgreementDetailView,BookingStartEndView

from .views import DeshboardSummaryAPIview,MonthlyTruckBookingAPIView,YearlyDashboardAPIView,YearlyDashboardRevenueAPIView,UserRetrieveUpdateDeleteAPIView, UserListAPIView

urlpatterns = [
   path("terms/", TermsAPIView.as_view(), name="terms"),
   path("privacy/", PrivacyAPIView.as_view(), name="privacy"),

   path('trucks/', TruckListCreateView.as_view(), name='truck-list-create'),
   path('trucks/<int:pk>/', TruckDetailAPIView.as_view(), name='truck-detail-update-delete'),


   path('price-managements/', PriceManagementListCreateAPIView.as_view(),name="price-list-create"),
   path('price-managements/<int:pk>/', PriceManagementDetailAPIView.as_view(), name="truck-detail-update-delete"),


   path('movers-management/',MoversManagementListCreateAPIView.as_view(),name='movers-management-list-create'),
   path('movers-management/<int:pk>/',MoversManagementDetailAPIView.as_view(),name='movers-management-detail'),


   path('notifications/', NotificationListAPIView.as_view(), name='notifications-list'),


   path("booking/update/<int:booking_id>/",BookingAdminUpdateView.as_view(),name="admin-booking-update"),
   path('bookings/start-end/<int:booking_id>/', BookingStartEndView.as_view(), name='booking-start-end'),


   path('agreements/<int:booking_id>/',BookingAgreementDetailView.as_view(),name='booking-agreement-detail'),


   path("dashboard-summary/", DeshboardSummaryAPIview.as_view(), name="dashboard-summary"),
   path("admin/monthly-truck-booking/",MonthlyTruckBookingAPIView.as_view(),name="admin-monthly-truck-booking"),
   path("admin/yearly-dashboard/",YearlyDashboardAPIView.as_view(),name="admin-yearly-dashboard"),
   path("admin/yearly-dashboard-revenue/",YearlyDashboardRevenueAPIView.as_view(),name="admin-yearly-dashboard-revenue"),



   path('users/', UserListAPIView.as_view(), name='user-list'),
   path('users/<int:user_id>/', UserRetrieveUpdateDeleteAPIView.as_view(), name='user-detail-update-delete'),




]