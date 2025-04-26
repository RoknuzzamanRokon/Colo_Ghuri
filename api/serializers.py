from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import models
from .models import Hotel, TourPackage, TourBooking
from django.utils import timezone

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'password2', 'point', 'created_at')
        read_only_fields = ('id', 'point', 'created_at')
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user

class UserBookingHistoryItemSerializer(serializers.ModelSerializer):
    """Serializer for individual booking items in user history"""
    package_name = serializers.CharField(source='package.name', read_only=True)
    package_destination = serializers.CharField(source='package.destination', read_only=True)
    package_start_date = serializers.DateField(source='package.start_date', read_only=True)
    package_end_date = serializers.DateField(source='package.end_date', read_only=True)

    class Meta:
        model = TourBooking
        fields = (
            'id', 'package_name', 'package_destination', 'package_start_date',
            'package_end_date', 'num_travelers', 'booking_date', 'status',
            'tracking_id', 'total_cost'
        )
        read_only_fields = fields # Make all fields read-only for history display

class UserDetailSerializer(serializers.ModelSerializer):
    """Serializer for User details including booking history and booking summary"""
    tour_bookings = UserBookingHistoryItemSerializer(many=True, read_only=True)
    booking_summary = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'point', 'created_at', 'booking_summary', 'tour_bookings')
        read_only_fields = ('id', 'point', 'created_at', 'booking_summary', 'tour_bookings')

    def get_booking_summary(self, obj):
        """Calculates booking summary statistics for the user"""
        total_booking_success = obj.tour_bookings.filter(status='Pending').count() # Assuming 'Pending' means successful booking
        total_booking_cancel = obj.tour_bookings.filter(status='Cancelled').count()

        total_return_point = obj.tour_bookings.filter(status='Cancelled').aggregate(total_refund=models.Sum('total_cost'))['total_refund'] or 0
        # To calculate total spent, we need to sum the total_cost of all bookings that are not cancelled.
        # Assuming total_cost is stored on the booking object when created.
        total_spend_point = obj.tour_bookings.exclude(status='Cancelled').aggregate(total_spent=models.Sum('total_cost'))['total_spent'] or 0

        return {
            "total_booking_success": total_booking_success,
            "total_booking_cancel": total_booking_cancel,
            "total_return_point": total_return_point,
            "total_spend_point": total_spend_point,
        }

class HotelSerializer(serializers.ModelSerializer):
    """Serializer for Hotel model"""
    class Meta:
        model = Hotel
        fields = '__all__'
        read_only_fields = ('hotel_id', 'created_at', 'updated_at')

class GivePointsSerializer(serializers.Serializer):
    """Serializer for giving points to a user"""
    user_id = serializers.IntegerField(required=True)
    points = serializers.FloatField(required=True)

class TourPackageSerializer(serializers.ModelSerializer):
    """Serializer for TourPackage model"""
    total_capacity = serializers.IntegerField(source='capacity', read_only=True)
    already_booking = serializers.SerializerMethodField(read_only=True)
    available_sit = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = TourPackage
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'total_capacity', 'already_booking', 'available_sit')

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.last_booking_date:
            representation['last_booking_date'] = instance.last_booking_date.strftime('%Y-%m-%d %H:%M:%S')
        return representation

    def get_already_booking(self, obj):
        """Calculate the number of already booked seats"""
        return obj.bookings.aggregate(total_booked=models.Sum('num_travelers'))['total_booked'] or 0

    def get_available_sit(self, obj):
        """Calculate the number of available seats"""
        return obj.capacity - (obj.bookings.aggregate(total_booked=models.Sum('num_travelers'))['total_booked'] or 0)

class TourBookingSerializer(serializers.ModelSerializer):
    """Serializer for TourBooking model"""
    package_tracking_id = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = TourBooking
        fields = ('package_tracking_id', 'num_travelers')
        read_only_fields = ('booking_date', 'total_cost', 'user', 'package') # Mark package as read-only here

class TourDetailSerializer(serializers.ModelSerializer):
    """Serializer for TourPackage model with booking details"""
    bookings = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()

    class Meta:
        model = TourPackage
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

    def get_bookings(self, obj):
        """Get total booked and available seats"""
        total_booked = obj.bookings.aggregate(total_booked=models.Sum('num_travelers'))['total_booked'] or 0
        available_sit = obj.capacity - total_booked
        return {'total_booked': total_booked, 'available_sit': available_sit}

    def get_is_active(self, obj):
        return timezone.now().date() <= obj.end_date
