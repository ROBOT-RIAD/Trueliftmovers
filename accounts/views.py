from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import status
from .serializers import RegisterSerializer,CustomTokenObtainPairSerializer,ChangePasswordSerializer,SendOTPSerializer, VerifyOTPSerializer, ResetPasswordSerializer
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny,IsAuthenticated
from .response import success_response
from rest_framework_simplejwt.views import TokenObtainPairView,TokenRefreshView

#swagger 
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi



# Create your views here.

#Register view

class RegisterView(APIView):
    permission_classes=[AllowAny]
    parser_classes=[MultiPartParser,FormParser]

    @swagger_auto_schema(
        operation_description="Register a new user and return JWT tokens",
        request_body=RegisterSerializer,
        tags=["Authentication"],
        responses={
            201: openapi.Response(
                description="User registered successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "data": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "access_token": openapi.Schema(type=openapi.TYPE_STRING),
                                "refresh_token": openapi.Schema(type=openapi.TYPE_STRING),
                                "user": openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        "id": openapi.Schema(type=openapi.TYPE_INTEGER),
                                        "email": openapi.Schema(type=openapi.TYPE_STRING),
                                        "role": openapi.Schema(type=openapi.TYPE_STRING),
                                    }
                                ),
                            },
                        ),
                    },
                ),
            )
        },
    )

    def post(self , request , *args,**kwargs):
        serializer = RegisterSerializer(data = request.data)

        serializer.is_valid(raise_exception=True)

        user , profile= serializer.save()
        refresh = RefreshToken.for_user(user)
        refresh['id'] = user.id
        refresh['email'] = user.email
        refresh['role'] = user.role
        access_token = str(refresh.access_token)

        data={
                'access_token': access_token,
                'refresh_token': str(refresh), 
                'user': {
                    'id' : user.id,
                    'email': user.email,
                    'role': user.role,
                }
            }
        return success_response(message="User registerd successfully",data=data,status_code=status.HTTP_201_CREATED)



#Token view

class LoginAPIView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = CustomTokenObtainPairSerializer
    parser_classes = [MultiPartParser, FormParser]

    @swagger_auto_schema(
        operation_description="Authenticate a user with email and password, returning JWT access and refresh tokens along with user details.",
        tags=["Authentication"],
        responses={
            200: openapi.Response(
                description="Login successful",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
                        "message": openapi.Schema(type=openapi.TYPE_STRING, example="Login successfully"),
                        "data": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "access": openapi.Schema(type=openapi.TYPE_STRING, example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."),
                                "refresh": openapi.Schema(type=openapi.TYPE_STRING, example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."),
                                "user": openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        "id": openapi.Schema(type=openapi.TYPE_INTEGER, example=10),
                                        "email": openapi.Schema(type=openapi.TYPE_STRING, example="gicagi2040@gamepec.com"),
                                        "role": openapi.Schema(type=openapi.TYPE_STRING, example="user"),
                                    },
                                ),
                            },
                        ),
                    },
                ),
            ),
            401: openapi.Response(
                description="Invalid credentials",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False),
                        "message": openapi.Schema(type=openapi.TYPE_STRING, example="No active account found with the given credentials"),
                        "data": openapi.Schema(type=openapi.TYPE_OBJECT, example={}),
                    },
                ),
            ),
        }
    )
    def post(self , request , *args, **kwargs):
        response = super().post(request , *args, **kwargs)
        return success_response(message="Login successfully",data=response.data,status_code=status.HTTP_200_OK)



#Refresh Token view

class CustomTokenRefresView(TokenRefreshView):
    permission_classes = [AllowAny]
    @swagger_auto_schema(
        tags=["Authentication"]
    )
    def post (self , request , *args, **kwargs):
        response = super().post(request , *args, **kwargs)
        return success_response(message="New Token get successfully",data=response.data,status_code=status.HTTP_200_OK)



#change password

class ChangePasswordApiView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser,FormParser]

    @swagger_auto_schema(
        operation_description="Change the current user's password using old and new password.",
        tags=["Authentication"],
        request_body=ChangePasswordSerializer,
        responses={
            200: openapi.Response(
                description="Password updated successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
                        "message": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example="Password updated successfully"
                        ),
                        "data": openapi.Schema(type=openapi.TYPE_OBJECT, example={}),
                    },
                )
            ),
            400: openapi.Response(
                description="Validation Error",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False),
                        "error": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            example={
                                "type": "ValidationError",
                                "message": "Old password is incorrect"
                            },
                        ),
                    },
                ),
            ),
            401: openapi.Response(
                description="Unauthorized",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False),
                        "error": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            example={
                                "type": "NotAuthenticated",
                                "message": "Authentication credentials were not provided."
                            },
                        ),
                    },
                ),
            ),
        },
    )
    
    def post(self , request , *args, **kwargs):
        serializer = ChangePasswordSerializer(data = request.data,context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return success_response(
            message="Password updated successfully",
            data={},
            status_code=status.HTTP_200_OK
        )



#forget password

class ForgetPasswordSendOTP(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Send OTP to user email for password reset",
        request_body=SendOTPSerializer,
        responses={
            201: openapi.Response(
                description="OTP sent successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
                        "message": openapi.Schema(type=openapi.TYPE_STRING, example="OTP sent successfully."),
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
        tags=["Forget Password"],
    )

    def post(self, request, *args, **kwargs):
        serializer = SendOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(message="OTP sent successfully.",data={},status_code=status.HTTP_201_CREATED)
    

#verify OTP

class ForgetPasswordVerifyOTP(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Verify the OTP sent to the user's email",
        request_body=VerifyOTPSerializer,
        responses={
            200: openapi.Response(
                description="OTP verified successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
                        "message": openapi.Schema(type=openapi.TYPE_STRING, example="OTP verified successfully."),
                        "data": openapi.Schema(type=openapi.TYPE_OBJECT, example={}),
                    },
                ),
            ),
            400: openapi.Response(
                description="Invalid or expired OTP",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False),
                        "message": openapi.Schema(type=openapi.TYPE_STRING, example="Invalid OTP"),
                        "data": openapi.Schema(type=openapi.TYPE_OBJECT, example={}),
                    },
                ),
            ),
        },
        tags=["Forget Password"],
    )

    def post(self, request, *args, **kwargs):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(message="OTP verified successfully.",data={},status_code=status.HTTP_200_OK)
    




class ForgetPasswordReset(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Reset the user's password after OTP verification",
        request_body=ResetPasswordSerializer,
        responses={
            200: openapi.Response(
                description="Password reset successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
                        "message": openapi.Schema(type=openapi.TYPE_STRING, example="Password reset successfully."),
                        "data": openapi.Schema(type=openapi.TYPE_OBJECT, example={}),
                    },
                ),
            ),
            400: openapi.Response(
                description="Invalid OTP or request data",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False),
                        "message": openapi.Schema(type=openapi.TYPE_STRING, example="Invalid OTP"),
                        "data": openapi.Schema(type=openapi.TYPE_OBJECT, example={}),
                    },
                ),
            ),
        },
        tags=["Forget Password"],
    )
    def post(self, request, *args, **kwargs):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(message="Password reset successfully.",data={},status_code=status.HTTP_200_OK)


