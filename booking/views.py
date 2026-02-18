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
from accounts.permissions import IsAdminRole,IsUserRole
from django.utils.dateparse import parse_date
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from rest_framework.pagination import PageNumberPagination


# Create your views here.

class BookingListCreateView(APIView):
    parser_classes = [MultiPartParser, FormParser]
    def get_permissions(self):
        if self.request.method == "POST":
            return [IsUserRole()]
        return [IsAuthenticated()]

    @swagger_auto_schema(
        operation_summary="Get booking list",
        operation_description="Get all bookings of the logged-in user",
        manual_parameters=[
            openapi.Parameter(
                'date',
                openapi.IN_QUERY,
                description="Filter bookings by specific date (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
                required=False
            ),
            openapi.Parameter(
                'status',
                openapi.IN_QUERY,
                description="Filter by booking status",
                type=openapi.TYPE_STRING,
                required=False
            ),
            openapi.Parameter(
                'truck_payment_status',
                openapi.IN_QUERY,
                description="Filter by truck payment status (true/false)",
                type=openapi.TYPE_BOOLEAN,
                required=False
            ),
            openapi.Parameter(
                'mover_payment_status',
                openapi.IN_QUERY,
                description="Filter by mover payment status (true/false)",
                type=openapi.TYPE_BOOLEAN,
                required=False
            ),
            openapi.Parameter(
                'page',
                openapi.IN_QUERY,
                description="Page number",
                type=openapi.TYPE_INTEGER,
                required=False
            ),
        ],
        responses={200: BookingGetSerializer(many=True)},
        tags=["Booking"]
    )
    def get(self, request):
        date_str = request.query_params.get('date', None)
        status_filter = request.query_params.get('status')
        truck_payment_filter = request.query_params.get('truck_payment_status')
        mover_payment_filter = request.query_params.get('mover_payment_status')

        if request.user.role == "admin":
            bookings = Booking.objects.all().order_by("-created_at")
            
            q_filter = Q()
            if date_str:
                filter_date = parse_date(date_str)
                if filter_date:
                    q_filter &= Q(created_at__date=filter_date)
            if status_filter:
                q_filter &= Q(status=status_filter)
            if truck_payment_filter is not None:
                truck_payment_bool = truck_payment_filter.lower() == 'true'
                q_filter &= Q(truck_payment_status=truck_payment_bool)
            if mover_payment_filter is not None:
                mover_payment_bool = mover_payment_filter.lower() == 'true'
                q_filter &= Q(mover_payment_status=mover_payment_bool)
            
            bookings = bookings.filter(q_filter)
        else:
            ten_days_ago = timezone.now() - timedelta(days=10)
            bookings = Booking.objects.filter(user=request.user,pickup_time__gte=ten_days_ago).order_by("-created_at")

        paginator = PageNumberPagination()
        paginator.page_size = 10
        paginated_bookings = paginator.paginate_queryset(bookings, request)
        serializer = BookingGetSerializer(paginated_bookings, many=True)
        paginated_data = {
            "count": paginator.page.paginator.count,
            "next": paginator.get_next_link(),
            "previous": paginator.get_previous_link(),
            "results": serializer.data
        }
        return success_response(
            message="Booking list retrieved successfully",
            data=paginated_data
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



class BookingRetrieveAPIView(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_summary="Retrieve a single booking",
        operation_description="Get a single booking by ID. Users can only view their own bookings, Admin can view all.",
        responses={200: BookingGetSerializer()},
        tags=["Booking"]
    )
    def get(self, request, booking_id):
        if request.user.role == "admin":
            booking = get_object_or_404(Booking, id=booking_id)
        else:
            booking = get_object_or_404(Booking, id=booking_id, user=request.user)

        serializer = BookingGetSerializer(booking)
        return success_response(
            message="Booking fetched successfully",
            data=serializer.data
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
