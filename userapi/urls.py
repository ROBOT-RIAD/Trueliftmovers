from django.urls import include, path
from support.views import SupportAPIView
from notifications.views import NotificationListAPIView,NotificationReadUpdateAPIView
from booking.views import BookingListCreateView,RejectBookingView,CreateBookingAgreementView,BookingAgreementDetailView,BookingEndRequestView

from payment.views import CreateCheckoutSessionView, PaymentSuccessView


urlpatterns = [
    
   path('support/', SupportAPIView.as_view(), name='support'),

   path('notifications/', NotificationListAPIView.as_view(), name='notifications-list'),
   path('notifications/read/<int:notification_id>/',NotificationReadUpdateAPIView.as_view(),name='notification-read'),


   path("bookings/", BookingListCreateView.as_view(), name="booking-list-create"),
   path('bookings/reject/<int:booking_id>/',RejectBookingView.as_view(),name='booking-reject'),
   path("bookings/end-request/<int:booking_id>/",BookingEndRequestView.as_view(),name="booking-end-request"),


   path('agreements/create/',CreateBookingAgreementView.as_view(),name='create-booking-agreement'),
   path('agreements/<int:booking_id>/',BookingAgreementDetailView.as_view(),name='booking-agreement-detail'),


   path('payment/create-checkout-session/', CreateCheckoutSessionView.as_view(), name='create-checkout-session'),
   path('payment/success/', PaymentSuccessView.as_view(), name='payment-success'),

]