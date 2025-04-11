from rest_framework import viewsets, generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from .models import Hotel
from .serializers import UserSerializer, UserDetailSerializer, HotelSerializer, GivePointsSerializer
from django.contrib.auth import authenticate
import base64

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
    
    if auth_header.startswith('Basic '):
        try:
            # Decode the Basic Auth string
            auth_decoded = base64.b64decode(auth_header[6:]).decode('utf-8')
            username, password = auth_decoded.split(':', 1)
            
            user = authenticate(username=username, password=password)
            
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
    return Response({
        'username': user.username,
        'points': user.point
    })

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
                'message': f'Successfully added {points} points to user with ID {user_id}'
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
