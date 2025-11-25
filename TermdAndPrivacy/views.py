from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from accounts.permissions import IsAdminRole
from .models import Terms, Privacy
from rest_framework.permissions import AllowAny

from .serializers import TermsSerialiser, PrivacySerializer
from accounts.response import success_response

# Swagger imports
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

# Create your views here.



class TermsAPIView(APIView):
    
    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAdminRole()]
        return [AllowAny()]

    @swagger_auto_schema(
        operation_description="Retrieve the latest Terms & Conditions",
        tags=["Terms Privacy"],
        responses={200: TermsSerialiser}
    )
    def get(self, request):
        instance = Terms.objects.first()
        if not instance:
            return success_response(
                "No Terms found",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )
        serializer = TermsSerialiser(instance)
        return success_response(
            "Terms retrieved successfully",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )

    @swagger_auto_schema(
        operation_description="Create or update Terms. Only one record allowed.",
        request_body=TermsSerialiser,
        tags=["Terms Privacy"],
        responses={
            200: openapi.Response(
                description="Terms updated successfully",
                schema=TermsSerialiser
            ),
            201: openapi.Response(
                description="Terms created successfully",
                schema=TermsSerialiser
            ),
            400: "Validation error"
        }
    )
    def post(self, request):
        instance = Terms.objects.first()

        if instance:
            serializer = TermsSerialiser(
                instance,
                data=request.data,
                partial=True,
                context={"request": request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return success_response(
                "Terms updated successfully",
                data=serializer.data,
                status_code=status.HTTP_200_OK
            )

        serializer = TermsSerialiser(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(
            "Terms created successfully",
            data=serializer.data,
            status_code=status.HTTP_201_CREATED
        )




class PrivacyAPIView(APIView):

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAdminRole()]
        return [AllowAny()]

    @swagger_auto_schema(
        operation_description="Retrieve the latest Privacy Policy",
        tags=["Terms Privacy"],
        responses={200: PrivacySerializer}
    )
    def get(self, request):
        instance = Privacy.objects.first()
        if not instance:
            return success_response(
                "No Privacy policy found",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )
        serializer = PrivacySerializer(instance)
        return success_response(
            "Privacy policy retrieved successfully",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )

    @swagger_auto_schema(
        operation_description="Create or update Privacy Policy. Only one record allowed.",
        request_body=PrivacySerializer,
        tags=["Terms Privacy"],
        responses={
            200: openapi.Response(
                description="Privacy policy updated successfully",
                schema=PrivacySerializer
            ),
            201: openapi.Response(
                description="Privacy policy created successfully",
                schema=PrivacySerializer
            ),
            400: "Validation error"
        }
    )
    def post(self, request):
        instance = Privacy.objects.first()

        if instance:
            serializer = PrivacySerializer(
                instance,
                data=request.data,
                partial=True,
                context={"request": request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return success_response(
                "Privacy policy updated successfully",
                data=serializer.data,
                status_code=status.HTTP_200_OK
            )

        serializer = PrivacySerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(
            "Privacy policy created successfully",
            data=serializer.data,
            status_code=status.HTTP_201_CREATED
        )




