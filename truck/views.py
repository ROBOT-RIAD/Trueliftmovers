from django.http import Http404
from django.shortcuts import render
from rest_framework.views import APIView
from accounts.permissions import IsAdminRole
from rest_framework.parsers import MultiPartParser,FormParser
from rest_framework import status
from accounts.response import success_response
from .serializers import TruckSerializer
from .models import Truck


#swagger
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.db.models import Q


# Create your views here.

class TruckListCreateView(APIView):
    permission_classes = [IsAdminRole]
    parser_classes = [MultiPartParser, FormParser]

    @swagger_auto_schema(
        operation_description="Get the list of all trucks (Admin only) with optional search and filters",
        manual_parameters=[
            openapi.Parameter('search', openapi.IN_QUERY, description="Search by truck_number_plate, driver_name, driver_phone_number, license_number", type=openapi.TYPE_STRING),
            openapi.Parameter('status', openapi.IN_QUERY, description="Filter by truck status (available/unavailable)", type=openapi.TYPE_STRING),
            openapi.Parameter('truck_size', openapi.IN_QUERY, description="Filter by truck size", type=openapi.TYPE_STRING),
        ],
        responses={200: TruckSerializer(many=True)},
        tags=['Trucks']
    )
    def get(self, request):
        trucks = Truck.objects.all()

        search_query = request.query_params.get('search')
        if search_query:
            trucks = trucks.filter(
                Q(truck_number_plate__icontains=search_query) |
                Q(driver_name__icontains=search_query) |
                Q(driver_phone_number__icontains=search_query) |
                Q(license_number__icontains=search_query)
            )

        status_filter = request.query_params.get('status')
        if status_filter:
            trucks = trucks.filter(status=status_filter)

        truck_size_filter = request.query_params.get('truck_size')
        if truck_size_filter:
            trucks = trucks.filter(truck_size=truck_size_filter)
            
        serializer = TruckSerializer(trucks, many=True)
        return success_response(message="Trucks retrieved successfully.", data=serializer.data,status_code=status.HTTP_200_OK)


    @swagger_auto_schema(
        operation_description="Create a new truck (Admin only)",
        request_body=TruckSerializer,
        responses={
            201: openapi.Response("Truck created successfully", TruckSerializer)
        },
        tags=['Trucks']
    )
    def post(self, request):
        serializer = TruckSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            truck = serializer.save()
            return success_response("Truck created successfully.", TruckSerializer(truck).data, 201)
        



class TruckDetailAPIView(APIView):
    permission_classes = [IsAdminRole]
    parser_classes = [MultiPartParser, FormParser]

    def get_object(self, pk):
        try:
            return Truck.objects.get(id=pk)
        except Truck.DoesNotExist:
            raise Http404

    @swagger_auto_schema(
        operation_description="Retrieve a truck details by ID (Admin only)",
        responses={200: TruckSerializer()},
        tags=['Trucks']
    )
    def get(self, request, pk):
        truck = self.get_object(pk)
        serializer = TruckSerializer(truck)
        return success_response("Truck retrieved successfully.", serializer.data)

    @swagger_auto_schema(
        operation_description="Partially update a truck by ID (Admin only)",
        request_body=TruckSerializer(partial=True),
        responses={200: TruckSerializer()},
        tags=['Trucks']
    )
    def patch(self, request, pk):
        truck = self.get_object(pk)
        serializer = TruckSerializer(truck, data=request.data, partial=True)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return success_response("Truck partially updated successfully.", serializer.data, status_code=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Delete a truck by ID (Admin only)",
        responses={200: "Truck deleted successfully"},
        tags=['Trucks']
    )
    def delete(self, request, pk):
        truck = self.get_object(pk)
        truck.delete()
        return success_response("Truck deleted successfully.", {}, 200)

