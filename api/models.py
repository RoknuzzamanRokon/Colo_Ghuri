from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils import timezone
import uuid

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

class TourPackage(models.Model):
    """
    Model to store tour package details
    """
    name = models.CharField(max_length=255)
    destination = models.CharField(max_length=255)
    duration = models.IntegerField(help_text="Duration in days")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    itinerary = models.TextField()
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(default=timezone.now)
    last_booking_date = models.DateTimeField(null=True, blank=True)
    capacity = models.PositiveIntegerField(default=10)
    images = models.ImageField(upload_to='tour_images/', null=True, blank=True)
    included_items = models.TextField(null=True, blank=True)
    excluded_items = models.TextField(null=True, blank=True)
    DIFFICULTY_CHOICES = [
        ('Easy', 'Easy'),
        ('Moderate', 'Moderate'),
        ('Difficult', 'Difficult'),
    ]
    difficulty_level = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='Easy')
    highlights = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class TourBooking(models.Model):
    """
    Model to handle user tour bookings
    """
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),
        ('Cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tour_bookings')
    package = models.ForeignKey(TourPackage, on_delete=models.CASCADE, related_name='bookings')
    booking_date = models.DateTimeField(auto_now_add=True)
    num_travelers = models.PositiveIntegerField(default=1)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    tracking_id = models.UUIDField(editable=False)

    def save(self, *args, **kwargs):
        # Calculate total cost before saving
        self.total_cost = self.package.price * self.num_travelers
        if not self.tracking_id:
            self.tracking_id = uuid.uuid4()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Booking for {self.package.name} by {self.user.username}"
