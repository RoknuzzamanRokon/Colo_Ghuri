from rest_framework import viewsets, generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from .models import Hotel
from .serializers import UserSerializer, UserDetailSerializer, HotelSerializer

User = get_user_model()

# Authentication Views
class RegisterView(generics.CreateAPIView):
    """View for user registration"""
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = UserSerializer

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
