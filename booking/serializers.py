from rest_framework import serializers
from truck.models import PriceManagement,MoversManagements,Truck
from .models  import Booking,BookingAgreement
from datetime import datetime
from django.utils import timezone
from .direaction import getdiractioninfo
from decimal import Decimal
from django.shortcuts import get_object_or_404
from .tasks import send_booking_email
from notifications.tasks import create_notification_task



class BookingCreateSerializer(serializers.ModelSerializer):
    preference_track = serializers.IntegerField(required = True)
    movers = serializers.IntegerField(required=False)

    class Meta:
        model = Booking
        fields =['preference_track','movers','pickup_time','pickup_address','pickup_lat','pickup_lng','drop_off_address','drop_lat','drop_lng','movable_items',]

    
    def validate(self, attrs):
        preference_track = attrs.get('preference_track')
        movers = attrs.get('movers')
        pickup_time = attrs.get('pickup_time')
        pickup_address = attrs.get('pickup_address')
        pickup_lat = attrs.get('pickup_lat')
        pickup_lng = attrs.get('pickup_lng')
        drop_off_address = attrs.get('drop_off_address')
        drop_lat = attrs.get('drop_lat')
        drop_lng = attrs.get('drop_lng')
        movable_items = attrs.get('movable_items')

        if pickup_time <= timezone.now():
            raise serializers.ValidationError({
                "pickup_time": "Pickup time must be in the future."
            })
        
        if not (-90 <= pickup_lat <= 90):
            raise serializers.ValidationError({"pickup_lat": "Invalid latitude value."})

        if not (-180 <= pickup_lng <= 180):
            raise serializers.ValidationError({"pickup_lng": "Invalid longitude value."})

        if not (-90 <= drop_lat <= 90):
            raise serializers.ValidationError({"drop_lat": "Invalid latitude value."})

        if not (-180 <= drop_lng <= 180):
                raise serializers.ValidationError({"drop_lng": "Invalid longitude value."})
        
        if pickup_lat == drop_lat and pickup_lng == drop_lng:
            raise serializers.ValidationError(
                "Pickup and drop-off locations cannot be the same."
            )
        if preference_track is not None and preference_track <= 0:
            raise serializers.ValidationError({
                "preference_track": "Invalid price preference ID."
            })
        
        if movers is not None and movers <= 0:
            raise serializers.ValidationError({
                "movers": "Invalid movers ID."
            })
        if movable_items:
            if not isinstance(movable_items, str):
                raise serializers.ValidationError({
                    "movable_items": "Movable items must be a text value."
                })

            if len(movable_items.strip()) < 5:
                raise serializers.ValidationError({
                    "movable_items": "Movable items description is too short."
                })
            
        if not isinstance(pickup_address, str) or len(pickup_address.strip()) < 5:
            raise serializers.ValidationError({
                "pickup_address": "Pickup address must be valid text."
            })

        if not isinstance(drop_off_address, str) or len(drop_off_address.strip()) < 5:
            raise serializers.ValidationError({
                "drop_off_address": "Drop-off address must be valid text."
            })
        
        return attrs
    
    def create(self, validated_data):
        request = self.context['request']
        preference_id = validated_data.pop('preference_track', None)
        movers_id = validated_data.pop('movers', None)

       
        if preference_id:
            preference = get_object_or_404(PriceManagement, id=preference_id)
           

        if movers_id: 
            movers = get_object_or_404(MoversManagements, id=movers_id)

        
        route_data = getdiractioninfo(
            validated_data['pickup_lat'],
            validated_data['pickup_lng'],
            validated_data['drop_lat'],
            validated_data['drop_lng'],
        )

        distance_km = Decimal(route_data['distance_meter']) / Decimal(1000)

        initial_price = 0

        if distance_km <= preference.minimum_distance:
            initial_price = Decimal(preference.minimum_charge)
        else:
            extra_distance = distance_km - Decimal(preference.minimum_distance)
            initial_price = (
                Decimal(preference.minimum_charge)
                + (extra_distance * Decimal(preference.unite_price))
            )


    
        result = {
            "user": request.user,
            "preference_track": {
                "id": preference.id,
                "truck_size": preference.truck_size,
                "minimum_distance": float(preference.minimum_distance),
                "minimum_charge": float(preference.minimum_charge),
                "unite_price": float(preference.unite_price),
                "create_at": preference.create_at.isoformat(),
                "update_at": preference.update_at.isoformat()
            },
            "movers": {
                "id": movers.id,
                "movers_number": movers.movers_number,
                "hour_rate": float(movers.hour_rate),
                "created_at": movers.created_at.isoformat(),
                "updated_at": movers.updated_at.isoformat()
            },
            "overview_polyline": route_data['overview_polyline'],
            "distance_meter": route_data['distance_meter'],
            "duration_second": route_data['duration_second'],
            "initial_price": float(initial_price),  
            "pickup_time": validated_data['pickup_time'],
            "pickup_address": validated_data['pickup_address'],
            "pickup_lat": float(validated_data['pickup_lat']),
            "pickup_lng": float(validated_data['pickup_lng']),
            "drop_off_address": validated_data['drop_off_address'],
            "drop_lat": float(validated_data['drop_lat']),
            "drop_lng": float(validated_data['drop_lng']),
            "movable_items": validated_data.get('movable_items', "")
        } 
        
        booking = Booking.objects.create(**result)


        create_notification_task.delay(
            user_id=request.user.id,
            title="New Booking Created",
            body=f"A new booking has been submitted.",
            data={
                "booking_id": booking.id,
                "user_id": booking.user.id if booking.user else None,
                "initial_price": float(booking.initial_price),
                "status": booking.status,
                "pickup_time": booking.pickup_time.isoformat() if booking.pickup_time else None,
                "pickup_address": booking.pickup_address,
                "drop_off_address": booking.drop_off_address,
                "distance_meter": booking.distance_meter,
                "duration_second": booking.duration_second,
                "created_at": booking.created_at.isoformat() if booking.created_at else None,
            },
            broadcast_user=False,
            broadcast_admin=True
        )

        send_booking_email.delay(booking.id)

        return booking




class BookingGetSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    truck = serializers.StringRelatedField()

    class Meta:
        model = Booking
        fields = ["id","user","truck","preference_track","movers","pickup_time","pickup_address","pickup_lat","pickup_lng","drop_off_address","drop_lat","drop_lng","movable_items","initial_price","final_price","movers_total","status","start_time","end_time","truck_payment_status","admin_note","mover_payment_status","overview_polyline","distance_meter","duration_second","created_at","updated_at", 
        ]




class BookingAdminUpdateSerializer(serializers.ModelSerializer):
    pickup_time = serializers.DateTimeField(required=False)

    class Meta:
        model = Booking
        fields = ["truck","admin_note","final_price",'pickup_time']

    def validate(self,attrs):
        final_price = attrs.get("final_price")
        truck = attrs.get("truck")

        if final_price is not None:
            if float(final_price) < 0:
                raise serializers.ValidationError({
                    "final_price": "Final price cannot be negative."
                })
            
        if truck:
            if not Truck.objects.filter(id=truck.id).exists():
                raise serializers.ValidationError({
                    "truck": "Selected truck does not exist."
                })
            
        return attrs
    

    def update(self, instance, validated_data):
        instance.truck = validated_data.get("truck", instance.truck)
        instance.admin_note = validated_data.get("admin_note", instance.admin_note)
        instance.final_price = validated_data.get("final_price", instance.final_price)
        instance.pickup_time = validated_data.get("pickup_time", instance.pickup_time)

        if instance.truck and instance.status == "pending":
            instance.status = "approved"

        instance.save()

        create_notification_task.delay(
            user_id=instance.user.id,
            title="Booking approved",
            body="Your booking has been approved by admin.",
            data={
                "booking_id": instance.id,
                "status": instance.status,
                "truck": str(instance.truck) if instance.truck else None,
                "final_price": float(instance.final_price) if instance.final_price else None,
                "pickup_time": instance.pickup_time.isoformat() if instance.pickup_time else None,
                "admin_note": instance.admin_note,
            },
            broadcast_user=True,
            broadcast_admin=False
        )

        return instance



class BookingRejectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ['id', 'status']

    def validate(self, attrs):
        booking = self.instance

        if not booking:
            raise serializers.ValidationError("Booking not found.")

        if booking.status == 'reject':
            raise serializers.ValidationError("Booking is already rejected.")

        
        if booking.status not in ['pending', 'approved', 'accepted']:
            raise serializers.ValidationError(f"Cannot reject booking with status '{booking.status}'.")
        
        return attrs
    

    def update(self, instance, validated_data):
        instance.status = 'reject'
        instance.save()

        create_notification_task.delay(
            user_id=instance.user.id,
            title="Booking Rejected",
            body="booking has been rejected",
            data={
                "booking_id": instance.id,
                "status": instance.status,
                "truck": str(instance.truck) if instance.truck else None,
                "final_price": float(instance.final_price) if instance.final_price else None,
                "pickup_time": instance.pickup_time.isoformat() if instance.pickup_time else None,
                "admin_note": instance.admin_note,
            },
            broadcast_user=False,
            broadcast_admin=True
        )

        return instance
    



class BookingAgreementSerializer(serializers.ModelSerializer):

    class Meta:
        model = BookingAgreement
        fields = ['id', 'booking', 'agreements', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, attrs):
        booking = attrs.get('booking')

        if not Booking.objects.filter(id=booking.id).exists():
            raise serializers.ValidationError("Booking does not exist.")

        if BookingAgreement.objects.filter(booking=booking).exists():
            raise serializers.ValidationError("Agreement already exists for this booking.")

        return attrs

    def create(self, validated_data):
        return BookingAgreement.objects.create(**validated_data)




class BookingstartendSerializer(serializers.ModelSerializer):
    status = serializers.ChoiceField(choices=[('start', 'Start'), ('end', 'End')])

    class Meta:
        model = Booking
        fields = ["status"]

    def validate(self, attrs):
        booking = self.instance

        new_status = attrs.get('status')

        
        if new_status == 'end' and not booking.start_time:
            raise serializers.ValidationError({
                "status": "Cannot end a booking that hasn't started"
            })

        if new_status == 'start' and booking.end_time:
            raise serializers.ValidationError({
                "status": "Cannot start a booking that has already ended"
            })
        
        return attrs
    

    def update(self, instance, validated_data):  
        new_status = validated_data.get('status')
        instance.status = new_status
        instance.save()


        data = {
            "booking_id": instance.id,
            "status": new_status,
            "pickup_address": instance.pickup_address,
            "drop_off_address": instance.drop_off_address,
            "pickup_time": instance.pickup_time.isoformat() if instance.pickup_time else None,
            "truck_payment_status": instance.truck_payment_status,
            "mover_payment_status": instance.mover_payment_status,
        }

        if new_status == 'end':
            data.update({
                "movers_total": float(instance.movers_total) if instance.movers_total else 0,
                "start_time": instance.start_time.isoformat() if instance.start_time else None,
                "end_time": instance.end_time.isoformat() if instance.end_time else None,
            })


        if instance.user:
            title = "Booking Started" if new_status == 'start' else "Booking Ended"
            body = f"Your booking #{instance.id} has {'started' if new_status == 'start' else 'ended'}."

            create_notification_task.delay(
                user_id=instance.user.id,
                title=title,
                body=body,
                data=data,
                broadcast_user=True,
                broadcast_admin=False
            )

        return instance



class BookingEndRequesttendSerializer(serializers.ModelSerializer):
    status = serializers.ChoiceField(choices=[('end_request', 'End Request')])

    class Meta:
        model = Booking
        fields = ["status"]

    def validate(self, attrs):
        booking = self.instance
        new_status = attrs.get('status')

        if booking.status != 'start':
            raise serializers.ValidationError({
                "status": "Cannot request end for a booking that hasn't started"
            })

        return attrs
    

    def update(self, instance, validated_data):
        instance.status = 'end_request'
        instance.save()
        title = "Booking End Request"
        body = f"User has requested to end Booking #{instance.id}."
        data = {
            "booking_id": instance.id,
            "status": instance.status,
            "user_id": instance.user.id if instance.user else None
        }
        
        create_notification_task.delay(
            user_id=instance.user.id if instance.user else None,  # optional: for reference
            title=title,
            body=body,
            data=data,
            broadcast_admin=True,
            broadcast_user=False
        )
        return instance
    
