from rest_framework import serializers
from truck.models import Truck
from booking.models import Booking
from accounts.models import User , Profile
from django.db.models import Sum, F, FloatField
from decimal import Decimal
import calendar

class DashbordSerializer(serializers.Serializer):
    total_trucks = serializers.SerializerMethodField()
    total_customers = serializers.SerializerMethodField()
    total_pending_booking = serializers.SerializerMethodField()

    def get_total_trucks(self, obj):
        return Truck.objects.count()
    
    def get_total_customers(self, obj):
        return User.objects.filter(role="user").count()
    
    def get_total_pending_booking(self, obj):
        return Booking.objects.filter(status="pending").count()
    


class MonthlyTruckBookingSerializer(serializers.ModelSerializer):
    total_bookings = serializers.SerializerMethodField()

    class Meta:
        model = Truck
        fields = ["truck_number_plate", "total_bookings"]

    def get_total_bookings(self, obj):
        month = self.context.get("month")
        year = self.context.get("year")

        bookings = Booking.objects.filter(
            truck=obj,
            created_at__year=year,
            created_at__month=month
        )
        return bookings.count()
    


class YearlyDashboardSerializer(serializers.Serializer):
    month = serializers.CharField()
    total_users = serializers.SerializerMethodField()
    total_revenue = serializers.SerializerMethodField()

    def get_total_users(self, obj):
        year = self.context.get("year")
        month_number = obj["month_number"]
        return User.objects.filter(
            date_joined__year=year,
            date_joined__month=month_number
        ).count()

    def get_total_revenue(self, obj):
        year = self.context.get("year")
        month_number = obj["month_number"]
        total = Booking.objects.filter(
            created_at__year=year,
            created_at__month=month_number,
            status="complete" 
        ).aggregate(
            total=Sum(F("final_price") + F("movers_total"), output_field=FloatField())
        )["total"]
        return total or Decimal("0.00")
    



class YearlyDashboardRevenueSerializer(serializers.Serializer):
    month = serializers.CharField()
    total_revenue = serializers.SerializerMethodField()
    yearly_percentage = serializers.SerializerMethodField()

    def get_total_revenue(self, obj):
        year = self.context.get("year")
        month_number = obj["month_number"]

        total = Booking.objects.filter(
            created_at__year=year,
            created_at__month=month_number,
            status="complete"
        ).aggregate(
            total=Sum(F("final_price") + F("movers_total"), output_field=FloatField())
        )["total"]

        return Decimal(total or 0)

    def get_yearly_percentage(self, obj):
        year = self.context.get("year")
        month_number = obj["month_number"]

    
        month_revenue = Booking.objects.filter(
            created_at__year=year,
            created_at__month=month_number,
            status="complete"
        ).aggregate(
            total=Sum(F("final_price") + F("movers_total"), output_field=FloatField())
        )["total"]
        month_revenue = Decimal(month_revenue or 0)

    
        yearly_total_revenue = Booking.objects.filter(
            created_at__year=year,
            status="complete"
        ).aggregate(
            total=Sum(F("final_price") + F("movers_total"), output_field=FloatField())
        )["total"]
        yearly_total_revenue = Decimal(yearly_total_revenue or 0)

        if yearly_total_revenue > 0:
            percentage = (month_revenue / yearly_total_revenue) * Decimal("100")
        else:
            percentage = Decimal("0.00")

        return round(percentage, 2)




class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='profile.full_name', allow_blank=True, required=False)
    phone = serializers.CharField(source='profile.phone', allow_blank=True, required=False)
    address = serializers.CharField(source='profile.address', allow_blank=True, required=False)
    country = serializers.CharField(source='profile.country', allow_blank=True, required=False)
    image = serializers.ImageField(source='profile.image', allow_null=True, required=False)
    recent_booking = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'role', 'date_joined',
            'full_name', 'phone', 'address', 'country', 'image',
            'recent_booking'
        ]
        read_only_fields = ['id', 'date_joined', 'recent_booking']

    def get_recent_booking(self, obj):
        booking = obj.bookings.order_by('-created_at').first()
        if booking:
            return {
                "id": booking.id,
                "truck_id": booking.truck.id if booking.truck else None,
                "status": booking.status,
                "pickup_time": booking.pickup_time,
                "drop_off_address": booking.drop_off_address,
                "final_price": booking.final_price,
                "movers_total": booking.movers_total,
                "created_at":booking.created_at
            }
        return None

    def validate(self, attrs):
        email = attrs.get('email')
        profile_data = attrs.get('profile', {})
        phone = profile_data.get('phone')
        full_name = profile_data.get('full_name')
        country = profile_data.get('country')

        user_id = self.instance.id if self.instance else None

        if email and User.objects.exclude(id=user_id).filter(email=email).exists():
            raise serializers.ValidationError({'email': 'Email already exists.'})

        if phone:
            phone = phone.strip()
            if not phone.startswith('+'):
                raise serializers.ValidationError({'phone': 'Phone number must start with a country code (e.g., +1, +44, +880).'})
            digits = phone[1:]
            if not digits.isdigit():
                raise serializers.ValidationError({'phone': 'Phone number must contain digits only after the country code.'})
            if len(digits) < 6 or len(digits) > 20:
                raise serializers.ValidationError({'phone': 'Phone number must be 8–20 digits (excluding +).'})

        if full_name and len(full_name) < 2:
            raise serializers.ValidationError({'full_name': 'Full name must be at least 2 characters.'})

        if country and not country.replace(' ', '').isalpha():
            raise serializers.ValidationError({'country': 'Country must contain letters only.'})

        return attrs

    def update(self, instance, validated_data):
        
        profile_data = validated_data.pop('profile', {})

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        profile, _ = Profile.objects.get_or_create(user=instance)
        for attr, value in profile_data.items():
            setattr(profile, attr, value)
        profile.save()

        return instance



