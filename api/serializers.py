from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import Hotel

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

class UserDetailSerializer(serializers.ModelSerializer):
    """Serializer for User details"""
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'point', 'created_at')
        read_only_fields = ('id', 'point', 'created_at')

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
