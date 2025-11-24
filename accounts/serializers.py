from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import User,Profile,PasswordReserOTP
from .tasks import send_otp_email
from django.contrib.auth.models import update_last_login
from django.contrib.auth import password_validation


#register Serializer

class RegisterSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(max_length=200,required=False,allow_blank=True,allow_null=True)
    phone = serializers.CharField(max_length=20,required= False,allow_blank=True,allow_null=True)
    address = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    country = serializers.CharField(max_length=100,required= False,allow_blank=True,allow_null=True)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'password', 'full_name', 'phone', 'address', 'country']
        extra_kwargs = {
            'password': {'write_only': True},
        }


    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")
        phone = attrs.get("phone")
        full_name = attrs.get("full_name")
        country = attrs.get("country")

        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError({"email": "Email already exists."})

        if password and len(password) < 6:
            raise serializers.ValidationError({"password": "Password must be at least 6 characters long."})

        if phone:
            phone = phone.strip()

            if not phone.startswith("+"):
                raise serializers.ValidationError({"phone": "Phone number must start with a country code (e.g., +1, +44, +880)."})
            
            digits = phone[1:]

            if not digits.isdigit():
                raise serializers.ValidationError({"phone": "Phone number must contain digits only after the country code."})

            country_code = digits[:3]
            if len(country_code) < 1:
                raise serializers.ValidationError({"phone": "Invalid country code."})

            number_part = digits[len(country_code):]

            if len(number_part) < 6:
                raise serializers.ValidationError({"phone": "Phone number must contain a valid number after the country code (minimum 6 digits)."})
            
            if not (8 <= len(digits) <= 20):
                raise serializers.ValidationError({"phone": "Phone number must be 8–20 digits (excluding +)."})


        if full_name and len(full_name) < 2:
            raise serializers.ValidationError({"full_name": "Full name must be at least 2 characters."})

        if country and not country.replace(" ", "").isalpha():
            raise serializers.ValidationError({"country": "Country must contain letters only."})

        return attrs


    def create(self, validated_data):
        full_name = validated_data.pop("full_name",None)
        phone = validated_data.pop("phone", None)
        address = validated_data.pop("address", None)
        country = validated_data.pop("country", None)

        email = validated_data.pop('email')
        password = validated_data.pop('password')

        user = User.objects.create_user(
            email = email,
            username=email,
            password = password
        )

        profile = Profile.objects.create(
            user = user,
            full_name = full_name,
            phone = phone,
            address = address,
            country = country
        )

        return user,profile
        


#login Serializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    email = serializers.EmailField()

    class Meta:
        model = User
        fields = ['email' , 'password']

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")


        try:
            user = User.objects.get(email = email)
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid email")
        
        if not user.check_password(password):
            raise serializers.ValidationError("Invalid Password")
        
        data = super().validate({'email': user.email, 'password': password})

        update_last_login(None, user)

        data['user'] = {
            'id': user.id,
            'email': user.email,
            'role': user.role,
        }

        return data
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims
        token['id'] = user.id
        token['email'] = user.email
        token['role'] = user.role

        return token



#change password

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only = True)
    new_password = serializers.CharField(write_only = True)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect")
        return value
    
    def validate_new_password(self, value):
        password_validation.validate_password(value)
        return value
    
    def save(self, **kwargs):
        user = self.context['request'].user
        new_password = self.validated_data["new_password"]
        user.set_password(new_password)
        user.save()
        return user



#Send OTP 

class SendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email does not exist.")
        return value
    
    def save(self):
        email = self.validated_data["email"]
        user = User.objects.get(email=email)
        otp_obj = PasswordReserOTP.objects.create(user=user)
        send_otp_email.delay(user.id, otp_obj.otp)
        return otp_obj




#Verify OTP

class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=4)

    def validate(self, attrs):
        email = attrs.get("email")
        otp = attrs.get("otp")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({"email": "User not found."})

        try:
            otp_obj = PasswordReserOTP.objects.get(
                user=user,
                otp=otp,
                is_verified=False
            )
        except PasswordReserOTP.DoesNotExist:
            raise serializers.ValidationError({"otp": "Invalid OTP."})

        if otp_obj.is_expired():
            raise serializers.ValidationError({"otp": "OTP expired."})

        attrs["user"] = user
        attrs["otp_obj"] = otp_obj
        return attrs
    
    def save(self):
        otp_obj = self.validated_data["otp_obj"]
        otp_obj.is_verified = True
        otp_obj.save()
        return otp_obj



#Reset Password

class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=4)
    new_password = serializers.CharField(write_only=True)

    def validate_new_password(self, value):
        password_validation.validate_password(value)
        return value
    
    def validate(self, attrs):
        email = attrs.get("email")
        otp = attrs.get("otp")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({"email": "User not found."})
        try:
            otp_obj = PasswordReserOTP.objects.get(user=user, otp=otp, is_verified=True)
        except PasswordReserOTP.DoesNotExist:
            raise serializers.ValidationError({"otp": "Invalid OTP."})
        attrs["user"] = user
        attrs["otp_obj"] = otp_obj
        return attrs
    
    def save(self):
        user = self.validated_data["user"]
        otp_obj = self.validated_data["otp_obj"]
        new_password = self.validated_data["new_password"]
        user.set_password(new_password)
        user.save()
        otp_obj.delete()
        return user

