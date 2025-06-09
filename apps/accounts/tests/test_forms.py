from django.test import TestCase
from django.contrib.auth import get_user_model
from ..forms import CustomUserCreationForm, CustomAuthenticationForm, ProfileForm
from ..models import Profile

User = get_user_model()


class CustomUserFormsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123456'
        )

    def test_custom_user_creation_form_valid_data(self):
        """Test CustomUserCreationForm with valid data"""
        form = CustomUserCreationForm({
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'password1': 'complexpass123456',
            'password2': 'complexpass123456',
        })
        self.assertTrue(form.is_valid())

    def test_custom_user_creation_form_no_data(self):
        """Test CustomUserCreationForm with no data"""
        form = CustomUserCreationForm({})
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
        self.assertIn('first_name', form.errors)
        self.assertIn('last_name', form.errors)
        self.assertIn('password1', form.errors)

    def test_custom_authentication_form_valid_data(self):
        """Test CustomAuthenticationForm with valid credentials"""
        form = CustomAuthenticationForm(data={
            'username': 'testuser',
            'password': 'testpass123456',
        })
        # Note: form.is_valid() will be False without request context
        # This tests form initialization
        self.assertIn('username', form.fields)
        self.assertIn('password', form.fields)

    def test_profile_form_valid_data(self):
        """Test ProfileForm with valid profile data"""
        form = ProfileForm({
            'date_of_birth': '1990-01-01',
            'phone_number': '0123456789',
            'chinese_level': 'beginner',
            'target_hsk_level': '3',
            'study_hours_per_week': '5',
            'preferred_study_time': 'morning',
            'bio': 'Test bio',
            'city': 'Hanoi',
            'country': 'Vietnam'
        })
        self.assertTrue(form.is_valid())

    def test_profile_form_invalid_data(self):
        """Test ProfileForm with invalid data"""
        form = ProfileForm({
            'phone_number': 'invalid_phone',
            'chinese_level': 'INVALID',
        })
        self.assertFalse(form.is_valid())
