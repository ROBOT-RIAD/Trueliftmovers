from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from .serializers import SupportSerializer
from accounts.response import success_response
from accounts.permissions import IsUserRole
from rest_framework.parsers import MultiPartParser, FormParser


#swagger
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi



class SupportAPIView(APIView):
    permission_classes = [IsUserRole]
    parser_classes=[MultiPartParser,FormParser]

    @swagger_auto_schema(
        operation_description="Create a new support request",
        request_body=SupportSerializer,
        responses={
            201: openapi.Response(
                description="Support request created successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
                        "message": openapi.Schema(type=openapi.TYPE_STRING, example="Support request created successfully."),
                        "data": openapi.Schema(type=openapi.TYPE_OBJECT, example={}),
                    },
                ),
            ),
            400: openapi.Response(
                description="Validation error",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False),
                        "error": openapi.Schema(type=openapi.TYPE_OBJECT),
                    },
                ),
            ),
        },
        tags=["Support"],
    )
    def post(self, request, *args, **kwargs):
        serializer = SupportSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        support = serializer.save()
        return success_response(
            message="Support request created successfully.",
            data={'id': support.id, 'title': support.title, 'text': support.text, 'resolved': support.resolved},
            status_code=status.HTTP_201_CREATED
        )

       

