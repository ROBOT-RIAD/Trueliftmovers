from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from .serializers import SupportSerializer,SupportUpdateSerializer
from accounts.response import success_response
from accounts.permissions import IsUserRole
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Support
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination


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

       

class SupportListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    # Add swagger query parameter for page number
    page_param = openapi.Parameter(
        "page",
        openapi.IN_QUERY,
        description="Page number for pagination",
        type=openapi.TYPE_INTEGER,
        required=False
    )

    @swagger_auto_schema(
        operation_description="Get paginated support requests of the logged-in user",
        manual_parameters=[page_param],
        responses={
            200: openapi.Response(
                description="Paginated list of support requests",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
                        "message": openapi.Schema(type=openapi.TYPE_STRING, example="All support requests fetched."),
                        "data": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "results": openapi.Schema(
                                    type=openapi.TYPE_ARRAY,
                                    items=openapi.Schema(
                                        type=openapi.TYPE_OBJECT,
                                        properties={
                                            "id": openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
                                            "title": openapi.Schema(type=openapi.TYPE_STRING, example="Issue with app"),
                                            "text": openapi.Schema(type=openapi.TYPE_STRING, example="App crashes on login"),
                                            "resolved": openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False),
                                            "created_at": openapi.Schema(type=openapi.TYPE_STRING, example="2026-02-21T10:00:00Z"),
                                            "updated_at": openapi.Schema(type=openapi.TYPE_STRING, example="2026-02-21T10:05:00Z"),
                                        },
                                    ),
                                ),
                                "count": openapi.Schema(type=openapi.TYPE_INTEGER, example=25),
                                "next": openapi.Schema(type=openapi.TYPE_STRING, example="http://api.example.com/support/all/?page=2", nullable=True),
                                "previous": openapi.Schema(type=openapi.TYPE_STRING, example=None, nullable=True),
                            }
                        ),
                    },
                ),
            )
        },
        tags=["Support"],
    )
    def get(self, request):
        supports = Support.objects.all().order_by("-created_at")
        paginator = PageNumberPagination()
        paginator.page_size = 10 
        paginated_qs = paginator.paginate_queryset(supports, request)

        data = [
            {
                "id": s.id,
                "title": s.title,
                "text": s.text,
                "resolved": s.resolved,
                "created_at": s.created_at,
                "updated_at": s.updated_at
            }
            for s in paginated_qs
        ]

        return paginator.get_paginated_response({
            "success": True,
            "message": "Support requests fetched successfully.",
            "results": data
        })

class SupportUpdateAPIView(APIView):
    parser_classes=[MultiPartParser,FormParser]
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_description="Update resolved status of a support request",
        request_body=SupportUpdateSerializer,
        responses={
            200: openapi.Response(
                description="Support request updated successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
                        "message": openapi.Schema(type=openapi.TYPE_STRING, example="Support request 'Issue with app' updated."),
                        "data": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "id": openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
                                "resolved": openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True)
                            }
                        )
                    }
                )
            ),
            404: openapi.Response(
                description="Support request not found",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False),
                        "error": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "type": openapi.Schema(type=openapi.TYPE_STRING, example="NotFound"),
                                "message": openapi.Schema(type=openapi.TYPE_STRING, example="Support request not found")
                            }
                        )
                    }
                )
            )
        },
        tags=["Support"],
    )
    def patch(self, request, pk):
        try:
            support = Support.objects.get(pk=pk)
        except Support.DoesNotExist:
            return Response({
                "success": False,
                "error": {"type": "NotFound", "message": "Support request not found"}
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = SupportUpdateSerializer(support, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return success_response(
            message=f"Support request '{support.title}' updated.",
            data={"id": support.id, "resolved": support.resolved}
        )