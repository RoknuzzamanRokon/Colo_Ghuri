from django.urls import path, include
from rest_framework import routers
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views import RegisterView, UserDetailView, HotelViewSet, get_user_points, hotel_search_basic_auth, give_points, AccountDetailView, update_hotel_admin, TourPackageViewSet, TourBookingViewSet, tour_detail_admin, UserBookingHistoryView

router = routers.DefaultRouter()
router.register(r'hotels', HotelViewSet, basename='hotel')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', TokenObtainPairView.as_view(), name='login'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='refresh'),
    path('auth/user/', UserDetailView.as_view(), name='user-detail'),
    path('auth/points/', get_user_points, name='user-points'),
    path('hotels/search/basic/', hotel_search_basic_auth, name='hotel-search-basic'),
    path('admin/give_points/', give_points, name='give-points'),
    path('account/', AccountDetailView.as_view(), name='account-detail'),
    path('admin/hotels/<int:hotel_id>/', update_hotel_admin, name='update-hotel-admin'),
    path('admin/tourpackages/<int:tour_id>/details/', tour_detail_admin, name='tour-detail-admin'),
    path('user/bookings/history/', UserBookingHistoryView.as_view(), name='user-booking-history'), # New endpoint for booking history
]

router.register(r'tourpackages', TourPackageViewSet, basename='tourpackage')
router.register(r'tourbookings', TourBookingViewSet, basename='tourbooking')
router.register(r'tourdetails', TourPackageViewSet, basename='tourdetail') # Register TourDetailViewSet

urlpatterns += router.urls
