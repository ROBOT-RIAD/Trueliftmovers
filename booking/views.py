from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.shortcuts import get_object_or_404

from .models import Booking,BookingAgreement
from .serializers import BookingCreateSerializer,BookingGetSerializer,BookingAdminUpdateSerializer,BookingRejectSerializer,BookingAgreementSerializer,BookingstartendSerializer,BookingEndRequesttendSerializer
from accounts.response import success_response
from rest_framework.parsers import MultiPartParser,FormParser
from accounts.permissions import IsAdminRole

# Create your views here.

class BookingListCreateView(APIView):
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Get booking list",
        operation_description="Get all bookings of the logged-in user",
        responses={200: BookingGetSerializer(many=True)},
        tags=["Booking"]
    )
    def get(self, request):
        bookings = Booking.objects.filter(user=request.user).order_by("-created_at")
        serializer = BookingGetSerializer(bookings, many=True)
        return success_response(
            message="Booking list retrieved successfully",
            data=serializer.data
        )
    
    @swagger_auto_schema(
        operation_summary="Create a booking",
        operation_description="Create a new truck booking",
        request_body=BookingCreateSerializer,
        responses={
            201: BookingGetSerializer,
            400: "Validation Error"
        },
        tags=["Booking"]
    )

    def post(self, request):
        serializer = BookingCreateSerializer(
            data=request.data,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        booking = serializer.save()

        response_serializer = BookingGetSerializer(booking)
        return success_response(
            message="Booking created successfully",
            data=response_serializer.data,
            status_code=status.HTTP_201_CREATED
        )



class BookingAdminUpdateView(APIView):
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAuthenticated]  

    @swagger_auto_schema(
        operation_summary="Admin updates booking",
        operation_description="Admin can update truck, final price, pickup time, and admin note of a booking",
        request_body=BookingAdminUpdateSerializer,
        responses={
            200: openapi.Response(
                description="Booking updated successfully",
                schema=BookingAdminUpdateSerializer
            ),
            400: "Validation Error",
            404: "Booking not found",
            403: "Permission denied"
        },
        tags=["Booking"]
    )
    def patch(self, request, booking_id):
        booking = get_object_or_404(Booking, id=booking_id)

        serializer = BookingAdminUpdateSerializer(
            booking,
            data=request.data,
            partial=True,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        updated_booking = serializer.save()

        response_serializer = BookingGetSerializer(updated_booking)
        return success_response(
            message="Booking updated successfully",
            data=response_serializer.data,
            status_code=status.HTTP_200_OK
        )




class RejectBookingView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Reject Booking",
        operation_description="Reject a single booking of the logged-in user",
        manual_parameters=[
            openapi.Parameter(
                "booking_id",
                openapi.IN_PATH,
                description="ID of the booking to reject",
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ],
        request_body=None,
        responses={
            200: openapi.Response(
                description="Booking rejected successfully",
                examples={
                    "application/json": {
                        "success": True,
                        "message": "Booking #123 rejected successfully.",
                        "data": {}
                    }
                }
            ),
        },
        tags=["Booking"]
    )
    def patch(self, request, booking_id):
        booking = get_object_or_404(Booking, id=booking_id, user=request.user)
        serializer = BookingRejectSerializer(instance=booking, data={}, partial=True)
        serializer.is_valid(raise_exception=True)
        updated_booking=serializer.save()
        response_serializer = BookingGetSerializer(updated_booking)
        return success_response(f"Booking #{booking.id} rejected successfully.", data=response_serializer.data)



class CreateBookingAgreementView(APIView):
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Create Booking Agreement",
        operation_description="Create a booking agreement for a specific booking. Only one agreement is allowed per booking.",
        tags=["Agreement"],
        request_body=BookingAgreementSerializer,
        responses={
            201: BookingAgreementSerializer,
            400: "Bad Request"
        }
    )

    def post(self, request):
        serializer = BookingAgreementSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        agreement = serializer.save()

        return success_response(
            message="Booking agreement created successfully.",
            data=BookingAgreementSerializer(agreement).data,
            status_code=status.HTTP_201_CREATED
        )
    


class BookingAgreementDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Get Booking Agreement",
        operation_description="Retrieve a single booking agreement using booking ID.",
        tags=["Agreement"],
        responses={
            200: BookingAgreementSerializer,
            404: "Not Found"
        }
    )

    def get(self, request, booking_id):
        agreement = BookingAgreement.objects.get(booking__id=booking_id)

        serializer = BookingAgreementSerializer(agreement)

        return success_response(
            message="Booking agreement retrieved successfully.",
            data=serializer.data
        )



class BookingStartEndView(APIView):
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Start or End Booking",
        operation_description="Update the status of a booking to 'start' or 'end'",
        manual_parameters=[
            openapi.Parameter(
                "booking_id",
                openapi.IN_PATH,
                description="ID of the booking to update",
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ],
        request_body=BookingstartendSerializer,  # must be class, not instance
        responses={
            200: openapi.Response("Booking details", BookingGetSerializer),  # remove ()
            400: "Validation error"
        },
        tags=["Booking"]
    )

    def patch(self, request, booking_id):
        booking = get_object_or_404(Booking, id=booking_id, user=request.user)
        serializer = BookingstartendSerializer(instance=booking, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated_booking = serializer.save()

        response_serializer = BookingGetSerializer(updated_booking)

        return success_response(
            f"Booking #{booking.id} {'started' if updated_booking.status == 'start' else 'ended'} successfully.",
            data=response_serializer.data
        )
    


class BookingEndRequestView(APIView):
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Request to End Booking",
        operation_description="User sends an end request for a booking that has started.",
        manual_parameters=[
            openapi.Parameter(
                "booking_id",
                openapi.IN_PATH,
                description="ID of the booking to request end",
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ],
        request_body=BookingEndRequesttendSerializer,
        responses={200: openapi.Response("Booking details", BookingGetSerializer)},
        tags=["Booking"]
    )
    def patch(self, request, booking_id):
        booking = get_object_or_404(Booking, id=booking_id, user=request.user)
        serializer = BookingEndRequesttendSerializer(instance=booking, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated_booking = serializer.save()

        response_serializer = BookingGetSerializer(updated_booking)

        return success_response(
            f"Booking #{booking.id} end request sent successfully.",
            data=response_serializer.data
        )
