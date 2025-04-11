from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils import timezone

class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser to include points
    """
    email = models.EmailField(unique=True)
    point = models.FloatField(default=settings.DEFAULT_USER_POINTS)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.username
    
    def has_sufficient_points(self):
        """Check if user has sufficient points to make a request"""
        return self.point > 0
    
    def deduct_points(self, amount=settings.POINT_DEDUCTION_PER_REQUEST):
        """Deduct points from user account"""
        if self.point >= amount:
            self.point -= amount
            self.save(update_fields=['point'])
            if self.point <= 0:
                # Invalidate JWT token by rotating the refresh token
                from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
                from rest_framework_simplejwt.tokens import RefreshToken
                
                try:
                    refresh_token = RefreshToken.for_user(self)
                    
                    # Blacklist all outstanding tokens for the user
                    OutstandingToken.objects.filter(user=self).delete()

                    # Blacklist the refresh token
                    BlacklistedToken.objects.create(token=str(refresh_token))
                except Exception as e:
                    # Handle any errors during token blacklisting
                    print(f"Error blacklisting token: {e}")
            return True
        return False

class Hotel(models.Model):
    """
    Hotel model to store hotel information
    """
    hotel_id = models.AutoField(primary_key=True)
    hotel_name = models.CharField(max_length=255)
    hotel_country = models.CharField(max_length=100)
    primary_picture = models.ImageField(upload_to='hotel_images/', null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    rating = models.FloatField(default=0.0, null=True, blank=True)
    price_range = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.hotel_name
