from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from .models import TourPackage, TourBooking
from django.utils import timezone

class CancelBookingTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpassword', email='test@example.com')
        self.client.force_authenticate(user=self.user)
        self.tour_package = TourPackage.objects.create(
            name='Test Tour',
            destination='Test Destination',
            duration=5,
            price=100.00,
            start_date=timezone.now().date() + timezone.timedelta(days=7),
            end_date=timezone.now().date() + timezone.timedelta(days=12),
        )
        self.booking = TourBooking.objects.create(
            user=self.user,
            package=self.tour_package,
            num_travelers=2,
        )
        self.booking.total_cost = self.tour_package.price * self.booking.num_travelers
        self.booking.save()

    def test_cancel_booking_within_20_minutes(self):
        self.booking.booking_date = timezone.now()
        self.booking.save()
        url = reverse('cancel-booking', args=[self.booking.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['refund_amount'], 200.0)
        self.assertEqual(response.data['booking_status'], 'Cancelled')
        self.user.refresh_from_db()
        self.assertEqual(self.user.point, 200.0)

    def test_cancel_booking_within_1_day(self):
        self.booking.booking_date = timezone.now() - timezone.timedelta(hours=12)
        self.booking.save()
        url = reverse('cancel-booking', args=[self.booking.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['refund_amount'], 180.0)
        self.assertEqual(response.data['booking_status'], 'Cancelled')
        self.user.refresh_from_db()
        self.assertEqual(self.user.point, 180.0)

    def test_cancel_booking_before_5_days(self):
        self.booking.booking_date = timezone.now() - timezone.timedelta(days=2)
        self.booking.save()
        url = reverse('cancel-booking', args=[self.booking.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['refund_amount'], 140.0)
        self.assertEqual(response.data['booking_status'], 'Cancelled')
        self.user.refresh_from_db()
        self.assertEqual(self.user.point, 140.0)

    def test_cancel_booking_on_last_booking_date(self):
        self.tour_package.start_date = timezone.now().date()
        self.tour_package.save()
        self.booking.booking_date = timezone.now() - timezone.timedelta(days=7)
        self.booking.save()
        url = reverse('cancel-booking', args=[self.booking.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['refund_amount'], 80.0)
        self.assertEqual(response.data['booking_status'], 'Cancelled')
        self.user.refresh_from_db()
        self.assertEqual(self.user.point, 80.0)

    def test_cancel_booking_not_found(self):
        url = reverse('cancel-booking', args=[999])  # Non-existent booking ID
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_cancel_booking_already_cancelled(self):
        self.booking.status = 'Cancelled'
        self.booking.save()
        url = reverse('cancel-booking', args=[self.booking.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cancel_booking_after_last_booking_date(self):
        self.tour_package.last_booking_date = timezone.now() - timezone.timedelta(days=1)
        self.tour_package.save()
        url = reverse('cancel-booking', args=[self.booking.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
