from rest_framework import viewsets, generics, permissions, status, serializers
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from .models import Hotel, TourPackage, TourBooking
from .serializers import UserSerializer, UserDetailSerializer, HotelSerializer, GivePointsSerializer, TourPackageSerializer, TourBookingSerializer, TourDetailSerializer
from django.contrib.auth import authenticate
import base64
from django.db import models
from django.utils import timezone
from decimal import Decimal
User = get_user_model()

# Authentication Views
class RegisterView(generics.CreateAPIView):
    """View for user registration"""
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = UserSerializer

@api_view(['POST'])
@permission_classes([AllowAny])
def hotel_search_basic_auth(request):
    """
    View for searching hotels using basic authentication (username and password)
    """
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    
    if auth_header and auth_header.startswith('Basic '):
        try:
            # Decode the Basic Auth string
            auth_decoded = base64.b64decode(auth_header[6:]).decode('utf-8')
            username, password = auth_decoded.split(':', 1)
            
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                # Authentication successful
                hotels = Hotel.objects.all()  # Or apply filtering based on search criteria
                serializer = HotelSerializer(hotels, many=True)
                return Response(serializer.data)
            else:
                # Authentication failed
                return Response(
                    {'error': 'Invalid credentials'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
        except Exception as e:
            return Response(
                {'error': 'Invalid Basic Auth header'},
                status=status.HTTP_400_BAD_REQUEST
            )
    else:
        return Response(
            {'error': 'Missing Basic Auth header'},
            status=status.HTTP_400_BAD_REQUEST
        )

class UserDetailView(generics.RetrieveAPIView):
    """View for retrieving user details"""
    permission_classes = (IsAuthenticated,)
    serializer_class = UserDetailSerializer
    
    def get_object(self):
        return self.request.user

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_points(request):
    """View for retrieving user points"""
    user = request.user
    if user.is_superuser:
        return Response({
            'username': user.username,
            'points': "I am supper admin"
        })
    else:
        return Response({
            'username': user.username,
            'points': user.point
        })

class AccountDetailView(generics.RetrieveAPIView):
    """View for retrieving account details of the logged-in user"""
    permission_classes = (IsAuthenticated,)
    serializer_class = UserDetailSerializer

    def get_object(self):
        return self.request.user

@api_view(['POST'])
@permission_classes([IsAdminUser])
def give_points(request):
    """
    View for super admins to give points to users
    """
    serializer = GivePointsSerializer(data=request.data)
    if serializer.is_valid():
        user_id = serializer.validated_data['user_id']
        points = serializer.validated_data['points']
        
        try:
            user = User.objects.get(pk=user_id)
            user.point += points
            user.save()
            return Response({
                'message': f'Successfully added {points} points to user with ID {user_id}',
                'username': user.username,
                'email': user.email
            })
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Hotel Views
class HotelViewSet(viewsets.ModelViewSet):
    """ViewSet for Hotel CRUD operations"""
    queryset = Hotel.objects.all()
    serializer_class = HotelSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        """
        Optionally filter hotels by country or name
        """
        queryset = Hotel.objects.all()
        country = self.request.query_params.get('country')
        name = self.request.query_params.get('name')

        if country:
            queryset = queryset.filter(hotel_country__icontains=country)
        if name:
            queryset = queryset.filter(hotel_name__icontains=name)

        return queryset

@api_view(['PUT'])
@permission_classes([IsAdminUser])
def update_hotel_admin(request, hotel_id):
    """
    View for super admins to update hotel information
    """
    try:
        hotel = Hotel.objects.get(pk=hotel_id)
    except Hotel.DoesNotExist:
        return Response(
            {'error': 'Hotel not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    serializer = HotelSerializer(hotel, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TourPackageViewSet(viewsets.ModelViewSet):
    """ViewSet for TourPackage CRUD operations"""
    queryset = TourPackage.objects.all()
    serializer_class = TourPackageSerializer
    permission_classes = [IsAdminUser] # Only allow admin users for CRUD operations
    lookup_field = 'tracking_id' # Use tracking_id for lookups

    def get_queryset(self):
        """
        Optionally filter tour packages by destination or name
        """
        queryset = TourPackage.objects.all()
        destination = self.request.query_params.get('destination')
        name = self.request.query_params.get('name')

        if destination:
            queryset = queryset.filter(destination__icontains=destination)
        if name:
            queryset = queryset.filter(name__icontains=name)

        return queryset

class TourDetailViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for listing tour packages with detailed information.
    This viewset is read-only and does not allow create, update, or delete actions.
    """
    queryset = TourPackage.objects.all()
    serializer_class = TourDetailSerializer
    permission_classes = [AllowAny] # Or set to IsAuthenticated if you want to protect this view
    lookup_field = 'tracking_id'

class TourBookingViewSet(viewsets.ModelViewSet):
    """ViewSet for TourBooking CRUD operations"""
    queryset = TourBooking.objects.all()
    serializer_class = TourBookingSerializer
    permission_classes = [IsAuthenticated]

    def dispatch(self, request, *args, **kwargs):
        # Decrease user points before processing the request
        if request.user.is_authenticated and not request.user.is_superuser:
            request.user.point -= 0.001
            if request.user.point < 0:
                request.user.point = 0
            request.user.save()
        return super().dispatch(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        """
        Override the create method to implement booking logic with point validation
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        package_tracking_id = serializer.validated_data['package_tracking_id']
        num_travelers = serializer.validated_data['num_travelers']

        try:
            package = TourPackage.objects.get(tracking_id=package_tracking_id)
        except TourPackage.DoesNotExist:
            return Response(
                {'error': 'Tour package not found with the provided tracking ID.'},
                status=status.HTTP_404_NOT_FOUND
            )

        total_cost = float(package.price) * num_travelers

        if package.last_booking_date and timezone.now().date() > package.last_booking_date.date():
            return Response(
                {'error': 'Booking for this tour package is closed.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if user.point < total_cost:
            return Response(
                {'error': 'Insufficient points to book this tour'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if tour has available capacity
        already_booked = package.bookings.aggregate(total_booked=models.Sum('num_travelers'))['total_booked'] or 0
        available_seats = package.capacity - already_booked
        if available_seats < num_travelers:
            return Response(
                {'error': 'This tour is fully booked. Please select another tour.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Deduct points from user account
        user.point -= total_cost
        user.save()

        # Create the booking
        import uuid
        booking = TourBooking.objects.create(user=user, package=package, num_travelers=num_travelers)
        booking.tracking_id = uuid.uuid4() # Assign a tracking ID to the booking
        booking.total_cost = total_cost # Save the calculated total_cost to the booking
        booking.save()


        return Response({
            'message': 'Booking successful!',
            'total_cost': total_cost,
            'remaining_points': user.point,
            'tour_name': package.name,
            'tour_location': package.destination,
            'tour_start_date': package.start_date,
            'tour_end_date': package.end_date,
            'tour_booking_tracking_id': str(booking.tracking_id),
            'total_booked_seats_history': already_booked + num_travelers, # Include current booking in history
        }, status=status.HTTP_201_CREATED)
    

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_booking(request):
    """
    View for canceling a tour booking using tracking IDs in the request body.
    """
    package_tracking_id = request.data.get('package_tracking_id')
    tour_booking_tracking_id = request.data.get('tour_booking_tracking_id')

    if not package_tracking_id or not tour_booking_tracking_id:
        return Response(
            {'error': 'Both package_tracking_id and tour_booking_tracking_id are required in the request body.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        booking = TourBooking.objects.get(
            package__tracking_id=package_tracking_id,
            tracking_id=tour_booking_tracking_id,
            user=request.user
        )
    except TourBooking.DoesNotExist:
        return Response({'error': 'Booking not found for the provided tracking IDs and user.'}, status=status.HTTP_404_NOT_FOUND)

    if booking.status == 'Cancelled':
        return Response({'message': 'Booking already cancelled'})

    now = timezone.now()
    time_difference = booking.booking_date - now
    
    # Check if cancellation is allowed based on last_booking_date
    if booking.package.last_booking_date and now.date() > booking.package.last_booking_date.date():
        return Response({'error': 'Cancellation not allowed after last booking date.'}, status=status.HTTP_400_BAD_REQUEST)

    refund_percentage = 0
    
    # Calculate refund based on cancellation time
    if time_difference <= timezone.timedelta(minutes=20):
        refund_percentage = 1.0  # 100% refund
    elif time_difference <= timezone.timedelta(days=1):
        refund_percentage = 0.9  # 90% refund
    elif (booking.package.start_date - now.date()).days > 5:
        refund_percentage = 0.7  # 70% refund
    elif now.date() == booking.package.start_date:
        refund_percentage = 0.4  # 40% refund
    else:
        refund_percentage = 0  # No refund

    # Refund points
    refund_amount = booking.total_cost * Decimal(str(refund_percentage))
    booking.user.point += float(refund_amount)
    booking.user.save()

    booking.status = 'Cancelled'
    booking.save()
    cancel_booking_time = timezone.now()


    return Response({
        'message': 'Booking cancelled successfully',
        'cancel_time': cancel_booking_time,
        'refund_amount': refund_amount,
        'remaining_points': booking.user.point,
        'booking_status': booking.status,
        'tour_booking_tracking_id': str(booking.tracking_id)
    })

# User booking history view
class UserBookingHistoryView(generics.ListAPIView):
    """
    View for retrieving booking history of the logged-in user
    """
    serializer_class = TourBookingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Return all tour bookings for the current user
        """
        user = self.request.user
        return TourBooking.objects.filter(user=user)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        active_bookings_count = queryset.filter(status='Pending', package__end_date__gte=timezone.now().date()).count()
        cancelled_bookings_count = queryset.filter(status='Cancelled').count()

        # Filter for tours that ended within the last 7 days
        seven_days_ago = timezone.now().date() - timezone.timedelta(days=1)
        recent_ended_tours = queryset.filter(
            package__end_date__gte=seven_days_ago,
            package__end_date__lt=timezone.now().date() # Ended before today
        ).order_by('-package__end_date') # Order by end date descending

        recent_ended_tours_data = [{
            'package': booking.package.id,
            'package_tracking_id': str(booking.package.tracking_id),
            'package_name': booking.package.name,
            'package_destination': booking.package.destination,
            'package_start_date': booking.package.start_date,
            'package_end_date': booking.package.end_date,
            'num_travelers': booking.num_travelers,
            'is_active': timezone.now().date() <= booking.package.end_date,
            'booking_date': booking.booking_date,
            'remaining_days_to_start': (booking.package.start_date - timezone.now().date()).days,
            'tour_booking_tracking_id': str(booking.tracking_id),
            'status': booking.status,
        } for booking in recent_ended_tours]

        # Find the nearest upcoming tour booking
        nearest_upcoming_tour = queryset.filter(
            package__start_date__gte=timezone.now().date()
        ).order_by('package__start_date').first()

        nearest_upcoming_tour_data = None
        if nearest_upcoming_tour:
            # Calculate total travelers for this package across all bookings by the user
            total_num_travelers = queryset.filter(
                package=nearest_upcoming_tour.package
            ).aggregate(total_travelers=models.Sum('num_travelers'))['total_travelers'] or 0

            nearest_upcoming_tour_data = {
                'package': nearest_upcoming_tour.package.id,
                'is_active': timezone.now().date() <= nearest_upcoming_tour.package.end_date,
                'remaining_days_to_start': (nearest_upcoming_tour.package.start_date - timezone.now().date()).days,
                'package_name': nearest_upcoming_tour.package.name,
                'package_destination': nearest_upcoming_tour.package.destination,
                'total_num_travelers': total_num_travelers,
                'traking_field': {
                    'package_tracking_id': str(nearest_upcoming_tour.package.tracking_id),
                    'tour_booking_tracking_id': str(nearest_upcoming_tour.tracking_id)
                },
                'time_status': {
                    'package_start_date': nearest_upcoming_tour.package.start_date,
                    'package_end_date': nearest_upcoming_tour.package.end_date,
                    'booking_date': nearest_upcoming_tour.booking_date
                },
                'current_status': nearest_upcoming_tour.status
            }


        return Response({
            'count': queryset.count(),
            'next': None,
            'previous': None,
            'status': {
                'active_booking': active_bookings_count,
                'cancel_booking': cancelled_bookings_count,
            },
            'resent_tour_status': recent_ended_tours_data,
            'nearest_upcoming_tour': nearest_upcoming_tour_data,
            'results': [{
                'package': booking.package.id,
                'package_tracking_id': str(booking.package.tracking_id),
                'package_name': booking.package.name,
                'package_destination': booking.package.destination,
                'package_start_date': booking.package.start_date,
                'package_end_date': booking.package.end_date,
                'num_travelers': booking.num_travelers,
                'is_active': timezone.now().date() <= booking.package.end_date,
                'booking_date': booking.booking_date,
                'remaining_days_to_start': (booking.package.start_date - timezone.now().date()).days,
                'tour_booking_tracking_id': str(booking.tracking_id),
                'status': booking.status,
            } for booking in queryset]
        })

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def tour_detail_admin(request, tracking_id):
    """
    View for super admins to get tour details with booking information using tracking ID
    """
    try:
        tour = TourPackage.objects.get(tracking_id=tracking_id)
    except TourPackage.DoesNotExist:
        return Response(
            {'error': 'Tour package not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Use the TourDetailSerializer which includes user list for admin
    serializer = TourDetailSerializer(tour) 
    return Response(serializer.data)




@api_view(['GET'])
@permission_classes([IsAuthenticated])
def tour_detail_user(request, tracking_id):
    """
    View for users to get tour details using tracking ID (without user list)
    """
    try:
        tour = TourPackage.objects.get(tracking_id=tracking_id)
    except TourPackage.DoesNotExist:
        return Response(
            {'error': 'Tour package not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Use the existing TourDetailSerializer from serializers.py
    serializer = TourDetailSerializer(tour)
    return Response(serializer.data)
