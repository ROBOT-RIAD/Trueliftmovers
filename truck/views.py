from django.http import Http404
from django.shortcuts import render
from rest_framework.views import APIView
from accounts.permissions import IsAdminRole
from rest_framework.parsers import MultiPartParser,FormParser
from rest_framework import status,permissions
from accounts.response import success_response
from .serializers import TruckSerializer,PriceManagementsSerializer,MoversManagemnetSerializer
from .models import Truck,PriceManagement,MoversManagements


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




class PriceManagementListCreateAPIView(APIView):  
    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdminRole()]
        return [permissions.IsAuthenticated()]

    @swagger_auto_schema(
        operation_summary="List price managements admin and user get also",
        operation_description="Get list of all price managements (Admin only) with optional filters",
        manual_parameters=[
            openapi.Parameter(
                'truck_size',
                openapi.IN_QUERY,
                description="Filter by truck size",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'minimum_distance',
                openapi.IN_QUERY,
                description="Filter by minimum distance",
                type=openapi.TYPE_NUMBER
            ),
        ],
        responses={200: PriceManagementsSerializer(many=True)},
        tags=["Price Management"]
    )

    def get(self, request):
        prices = PriceManagement.objects.all()

        truck_size = request.query_params.get('truck_size')
        if truck_size:
            prices = prices.filter(truck_size=truck_size)

        minimum_distance = request.query_params.get('minimum_distance')
        if minimum_distance:
            prices = prices.filter(minimum_distance=minimum_distance)

        serializer = PriceManagementsSerializer(prices, many=True)
        return success_response(
            message="Price management list retrieved successfully.",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )
    

    @swagger_auto_schema(
        operation_summary="Create price management",
        operation_description="Create a new price management (Admin only)",
        request_body=PriceManagementsSerializer,
        responses={201: PriceManagementsSerializer},
        tags=["Price Management"]
    )

    def post(self , request):
        serializer = PriceManagementsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(message="Price management created successfully",data=serializer.data,status_code=status.HTTP_201_CREATED)




class PriceManagementDetailAPIView(APIView):
    permission_classes = [IsAdminRole]
    parser_classes = [MultiPartParser, FormParser]

    def get_object(self, pk):
        try:
            return PriceManagement.objects.get(id=pk)
        except PriceManagement.DoesNotExist:
            raise Http404

    @swagger_auto_schema(
        operation_summary="Retrieve price management",
        operation_description="Retrieve price management details by ID (Admin only)",
        responses={200: PriceManagementsSerializer()},
        tags=["Price Management"]
    )
    def get(self, request, pk):
        price = self.get_object(pk)
        serializer = PriceManagementsSerializer(price)
        return success_response(
            message="Price management retrieved successfully.",
            data=serializer.data
        )

    @swagger_auto_schema(
        operation_summary="Update price management",
        operation_description="Partially update price management by ID (Admin only)",
        request_body=PriceManagementsSerializer(partial=True),
        responses={200: PriceManagementsSerializer()},
        tags=["Price Management"]
    )
    def patch(self, request, pk):
        price = self.get_object(pk)
        serializer = PriceManagementsSerializer(
            price, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(
            message="Price management updated successfully.",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )

    @swagger_auto_schema(
        operation_summary="Delete price management",
        operation_description="Delete price management by ID (Admin only)",
        responses={200: "Price management deleted successfully"},
        tags=["Price Management"]
    )
    def delete(self, request, pk):
        price = self.get_object(pk)
        price.delete()
        return success_response(
            message="Price management deleted successfully.",
            data={},
            status_code=status.HTTP_200_OK
        )



class MoversManagementListCreateAPIView(APIView):
    parser_classes = [MultiPartParser, FormParser]
    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdminRole()]
        return [permissions.IsAuthenticated()]

    @swagger_auto_schema(
        operation_summary="List movers managements admin and user gt also",
        operation_description="Get list of all movers managements (Admin only) with optional filters",
        manual_parameters=[
            openapi.Parameter(
                'movers_number',
                openapi.IN_QUERY,
                description="Filter by movers number",
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                'hour_rate',
                openapi.IN_QUERY,
                description="Filter by hour rate",
                type=openapi.TYPE_NUMBER
            ),
        ],
        responses={200: MoversManagemnetSerializer(many=True)},
        tags=["Movers Management"]
    )
    def get(self, request):
        movers = MoversManagements.objects.all()

        movers_number = request.query_params.get('movers_number')
        if movers_number:
            movers = movers.filter(movers_number=movers_number)

        hour_rate = request.query_params.get('hour_rate')
        if hour_rate:
            movers = movers.filter(hour_rate=hour_rate)

        serializer = MoversManagemnetSerializer(movers, many=True)
        return success_response(
            message="Movers management list retrieved successfully.",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )

    @swagger_auto_schema(
        operation_summary="Create movers management",
        operation_description="Create a new movers management (Admin only)",
        request_body=MoversManagemnetSerializer,
        responses={201: MoversManagemnetSerializer},
        tags=["Movers Management"]
    )
    def post(self, request):
        serializer = MoversManagemnetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(
            message="Movers management created successfully.",
            data=serializer.data,
            status_code=status.HTTP_201_CREATED
        )



class MoversManagementDetailAPIView(APIView):
    permission_classes = [IsAdminRole]
    parser_classes = [MultiPartParser, FormParser]

    def get_object(self, pk):
        try:
            return MoversManagements.objects.get(id=pk)
        except MoversManagements.DoesNotExist:
            raise Http404

    @swagger_auto_schema(
        operation_summary="Retrieve movers management",
        operation_description="Retrieve movers management details by ID (Admin only)",
        responses={200: MoversManagemnetSerializer()},
        tags=["Movers Management"]
    )
    def get(self, request, pk):
        mover = self.get_object(pk)
        serializer = MoversManagemnetSerializer(mover)
        return success_response(
            message="Movers management retrieved successfully.",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )

    @swagger_auto_schema(
        operation_summary="Update movers management",
        operation_description="Partially update movers management by ID (Admin only)",
        request_body=MoversManagemnetSerializer(partial=True),
        responses={200: MoversManagemnetSerializer()},
        tags=["Movers Management"]
    )
    def patch(self, request, pk):
        mover = self.get_object(pk)
        serializer = MoversManagemnetSerializer(
            mover, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(
            message="Movers management updated successfully.",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )

    @swagger_auto_schema(
        operation_summary="Delete movers management",
        operation_description="Delete movers management by ID (Admin only)",
        responses={200: "Movers management deleted successfully"},
        tags=["Movers Management"]
    )
    def delete(self, request, pk):
        mover = self.get_object(pk)
        mover.delete()
        return success_response(
            message="Movers management deleted successfully.",
            data={},
            status_code=status.HTTP_200_OK
        )
