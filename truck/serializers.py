from rest_framework import serializers
from .models import Truck
import datetime
import os


class TruckSerializer(serializers.ModelSerializer):
    truck_number_plate = serializers.CharField(max_length=300, required=False)
    class Meta:
        model = Truck
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

    def validate(self, attrs):
        
        # --------- TRUCK NUMBER PLATE (Required & Unique) ----------
        if self.instance:
            old_plate = self.instance.truck_number_plate
        else:
            old_plate = None

        plate = attrs.get('truck_number_plate', old_plate)

        if not plate and not self.partial:
            raise serializers.ValidationError("Truck number plate is required.")

        if 'truck_number_plate' in attrs:
            plate = attrs['truck_number_plate']
            if not plate:
                raise serializers.ValidationError("Truck number plate cannot be empty.")
            if Truck.objects.exclude(id=self.instance.id if self.instance else None).filter(truck_number_plate=plate).exists():
                raise serializers.ValidationError("This truck number plate already exists.")

        # ---------- TRUCK SIZE ----------
        truck_size = attrs.get('truck_size')
        if truck_size and len(truck_size) < 2:
            raise serializers.ValidationError("Truck size must be at least 2 characters.")

        # ---------- TRUCK CAPACITY ----------
        capacity = attrs.get('truck_capacity')
        if capacity and len(capacity) < 1:
            raise serializers.ValidationError("Truck capacity cannot be empty.")

        # ---------- STATUS ----------
        status = attrs.get('status')
        if status and status not in ['available', 'unavailable']:
            raise serializers.ValidationError("Status must be either 'available' or 'unavailable'.")

        # ---------- DRIVER NAME ----------
        name = attrs.get('driver_name')
        if name and len(name) < 3:
            raise serializers.ValidationError("Driver name must be at least 3 characters long.")

        # ---------- PHONE NUMBER ----------
        phone = attrs.get('driver_phone_number')
        if phone:
            if not phone.isdigit():
                raise serializers.ValidationError("Driver phone number must be digits only.")
            if len(phone) < 6:
                raise serializers.ValidationError("Driver phone number is too short.")

        # ---------- LICENSE NUMBER ----------
        license = attrs.get('license_number')
        if license and len(license) < 5:
            raise serializers.ValidationError("License number must be at least 5 characters.")

        # ---------- INSPECTION DATE ----------
        inspection_date = attrs.get('inspection_date')
        if inspection_date and inspection_date > datetime.date.today():
            raise serializers.ValidationError("Inspection date cannot be in the future.")

        return attrs
    


    def create(self, validated_data):
        return Truck.objects.create(**validated_data)
    

    def update(self, instance, validated_data):
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        return instance


