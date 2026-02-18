from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from accounts.response import success_response
from django.shortcuts import get_object_or_404

from .models import Notification
from .serializers import NotificationSerializer


#swagger 
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

# Create your views here.


class NotificationListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Get notifications",
        operation_description=(
            "Retrieve notifications for the authenticated user.\n\n"
            "- **Admin** (`role=admin`) receives **all notifications**\n"
            "- **Normal users** receive **only their own notifications**"
        ),
        responses={
            200: openapi.Response(
                description="Notifications fetched successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "data": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Items(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    "id": openapi.Schema(type=openapi.TYPE_INTEGER),
                                    "user": openapi.Schema(type=openapi.TYPE_INTEGER),
                                    "title": openapi.Schema(type=openapi.TYPE_STRING),
                                    "body": openapi.Schema(type=openapi.TYPE_STRING),
                                    "data": openapi.Schema(type=openapi.TYPE_OBJECT),
                                    "read": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                    "created_at": openapi.Schema(type=openapi.TYPE_STRING, format="date-time"),
                                }
                            )
                        )
                    }
                )
            ),
            401: "Unauthorized"
        },
        tags=["Notifications"]
    )

    def get(self, request):
        user = request.user
        if user.role == "admin":
            notifications = Notification.objects.filter(admin_notification=True).order_by("-created_at")
        else:
            notifications = Notification.objects.filter(user=user,user_notification=True).order_by("-created_at")

        serializer = NotificationSerializer(notifications, many=True)
        return success_response(
            message="Notifications fetched successfully",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )
    


class NotificationReadUpdateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Mark notification as read",
        operation_description=(
            "Marks a specific notification as **read** for the authenticated user.\n\n"
            "- Users can update **only their own notifications**\n"
            "- Only the `read` field is updated\n"
            "- Request body is not required"
        ),
        responses={
            200: openapi.Response(
                description="Notification marked as read",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "data": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "id": openapi.Schema(type=openapi.TYPE_INTEGER),
                                "read": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                            }
                        )
                    }
                )
            ),
            401: "Unauthorized",
            404: "Notification not found"
        },
        tags=["Notifications"]
    )

    def patch(self, request, notification_id):
        user = request.user
        notification = get_object_or_404(
            Notification,
            id=notification_id,
            user=user
        )
        notification.read = True
        notification.save(update_fields=["read", "updated_at"])
        return success_response(
            message="Notification marked as read",
            data={
                "id": notification.id,
                "read": notification.read
            },
            status_code=status.HTTP_200_OK
        )



