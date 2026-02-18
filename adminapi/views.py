from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .serializers import DashbordSerializer,MonthlyTruckBookingSerializer,YearlyDashboardSerializer,YearlyDashboardRevenueSerializer,UserSerializer
from accounts.response import success_response
from drf_yasg.utils import swagger_auto_schema
from truck.models import Truck
from drf_yasg import openapi
from rest_framework.parsers import MultiPartParser,FormParser
from django.utils import timezone
import calendar
from django.shortcuts import get_object_or_404
from accounts.models import User
# Create your views here.

class DeshboardSummaryAPIview(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_summary="Dashboard Summary",
        operation_description="Retrieve dashboard statistics including total trucks, total customers, and total pending bookings.",
        responses={200: DashbordSerializer},
        tags=["Dashboard"]
    )
    def get(self, request):
        serializer = DashbordSerializer(instance={})
        return success_response(
            message="Dashboard summary fetched successfully",
            data=serializer.data,
        )
    


class MonthlyTruckBookingAPIView(APIView):
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Admin Monthly Truck Booking Report",
        operation_description="Admin-only endpoint to get total bookings per truck for a specific month and year.",
        manual_parameters=[
            openapi.Parameter(
                "month",
                openapi.IN_QUERY,
                description="Month number (1-12)",
                type=openapi.TYPE_INTEGER,
                required=False
            ),
            openapi.Parameter(
                "year",
                openapi.IN_QUERY,
                description="Year (e.g., 2026)",
                type=openapi.TYPE_INTEGER,
                required=False
            ),
        ],
        responses={200: MonthlyTruckBookingSerializer(many=True)},tags=["Dashboard"]

    )
    def get(self, request):
        now = timezone.now()

        month = request.query_params.get("month", now.month)
        year = request.query_params.get("year", now.year)

        trucks = Truck.objects.all()

        serializer = MonthlyTruckBookingSerializer(
            trucks,
            many=True,
            context={
                "month": int(month),
                "year": int(year),
            }
        )

        return success_response(
            message="Monthly truck booking report fetched successfully",
            data={
                "data":serializer.data,
                "month":int(month)
            },
            status_code=status.HTTP_200_OK
        )



class YearlyDashboardAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Yearly Dashboard Report",
        operation_description="Admin-only endpoint. Returns 12-month summary (total users & total revenue). Defaults to current year.",
        manual_parameters=[
            openapi.Parameter(
                "year",
                openapi.IN_QUERY,
                description="Optional year (e.g., 2026)",
                type=openapi.TYPE_INTEGER,
                required=False
            ),
        ],
        responses={200: YearlyDashboardSerializer(many=True)},
        tags=["Dashboard"]
    )
    def get(self, request):

        now = timezone.now()
        year = int(request.query_params.get("year", now.year))

        months = [{"month": calendar.month_abbr[i], "month_number": i} for i in range(1, 13)]

        serializer = YearlyDashboardSerializer(months, many=True, context={"year": year})

        return success_response(
            message="Yearly dashboard report fetched successfully",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )




class YearlyDashboardRevenueAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Yearly Dashboard Revenue Report",
        operation_description="Admin-only endpoint. Returns 12-month revenue summary with yearly percentage. Defaults to current year.",
        manual_parameters=[
            openapi.Parameter(
                "year",
                openapi.IN_QUERY,
                description="Optional year (e.g., 2026)",
                type=openapi.TYPE_INTEGER,
                required=False
            ),
        ],
        responses={200: YearlyDashboardRevenueSerializer(many=True)},
        tags=["Dashboard"]
    )
    def get(self, request):
        now = timezone.now()
        year = int(request.query_params.get("year", now.year))

        # Prepare months for serializer
        months = [{"month": calendar.month_abbr[i], "month_number": i} for i in range(1, 13)]

        serializer = YearlyDashboardRevenueSerializer(months, many=True, context={"year": year})

        return success_response(
            message="Yearly dashboard revenue report fetched successfully",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )



class UserListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="List all users",
        operation_description="Admin-only: Get a list of all users with their most recent booking",
        responses={200: UserSerializer(many=True)},
        tags=["Users Management"]
    )
    def get(self, request):
        users = User.objects.filter(role='user').order_by('-date_joined')
        serializer = UserSerializer(users, many=True)
        return success_response(
            message="Users fetched successfully",
            data=serializer.data
        )
    


class UserRetrieveUpdateDeleteAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Retrieve single user",
        operation_description="Admin-only: Get a single user by ID with recent booking info",
        responses={200: UserSerializer()},
        tags=["Users Management"]
    )
    def get(self, request, user_id):
        user = get_object_or_404(User, id=user_id,role='user')
        serializer = UserSerializer(user)
        return success_response(
            message="User fetched successfully",
            data=serializer.data
        )

    @swagger_auto_schema(
        operation_summary="Update user",
        operation_description="Admin-only: Update user profile info (password not allowed)",
        request_body=UserSerializer,
        responses={200: UserSerializer()},
        tags=["Users Management"]
    )
    def patch(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        serializer = UserSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(
            message="User updated successfully",
            data=serializer.data
        )

    @swagger_auto_schema(
        operation_summary="Delete user",
        operation_description="Admin-only: Delete a user by ID",
        responses={200: "User deleted successfully"},
        tags=["Users Management"]
    )
    def delete(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        user.delete()
        return success_response(
            message="User deleted successfully"
        )
    

