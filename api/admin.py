from django.contrib import admin
from .models import Hotel, User

admin.site.register(Hotel)
admin.site.register(User)
from .models import TourPackage, TourBooking

admin.site.register(TourPackage)
admin.site.register(TourBooking)
