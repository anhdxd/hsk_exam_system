"""
Authentication tests for HSK Exam System

Tests for user authentication, registration, login/logout functionality
using the custom user model and authentication system.
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from ..models import CustomUser, Profile
from ..forms import CustomUserCreationForm, CustomAuthenticationForm

User = get_user_model()

class CustomUserModelTest(TestCase):
    """Test cases for CustomUser model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )

    def test_user_creation(self):
        """Test that user is created correctly"""
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.get_full_name(), 'Test User')
        self.assertTrue(self.user.check_password('testpass123'))

    def test_user_authentication(self):
        """Test user password authentication"""
        user = User.objects.get(email='test@example.com')
        self.assertTrue(user.check_password('testpass123'))
        self.assertFalse(user.check_password('wrongpassword'))

    def test_user_properties(self):
        """Test user default properties"""
        self.assertTrue(self.user.is_active)
        self.assertFalse(self.user.is_staff)
        self.assertFalse(self.user.is_superuser)
        self.assertFalse(self.user.is_verified)

    def test_profile_creation(self):
        """Test that profile is automatically created for new users"""
        self.assertTrue(hasattr(self.user, 'profile'))
        self.assertIsInstance(self.user.profile, Profile)

    def test_user_string_representation(self):
        """Test user __str__ method"""
        expected = f"Test User ({self.user.email})"
        self.assertEqual(str(self.user), expected)

    def test_profile_completion_check(self):
        """Test profile completion property"""
        # Initially profile should not be complete
        self.assertFalse(self.user.is_profile_complete)
        
        # Complete the profile
        profile = self.user.profile
        profile.date_of_birth = '1990-01-01'
        profile.target_hsk_level = 3
        profile.chinese_level = 'intermediate'
        profile.save()
        
        # Now it should be complete
        self.assertTrue(self.user.is_profile_complete)


class AuthenticationViewsTest(TestCase):
    """Test cases for authentication views"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )

    def test_login_view_get(self):
        """Test login view GET request"""
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Đăng nhập')
        self.assertIsInstance(response.context['form'], CustomAuthenticationForm)

    def test_login_view_post_valid(self):
        """Test login with valid credentials"""
        response = self.client.post(reverse('accounts:login'), {
            'username': 'test@example.com',
            'password': 'testpass123'
        })
        self.assertRedirects(response, reverse('accounts:dashboard'))

    def test_login_view_post_invalid(self):
        """Test login with invalid credentials"""
        response = self.client.post(reverse('accounts:login'), {
            'username': 'test@example.com',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'form')

    def test_register_view_get(self):
        """Test register view GET request"""
        response = self.client.get(reverse('accounts:register'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Đăng ký')
        self.assertIsInstance(response.context['form'], CustomUserCreationForm)

    def test_register_view_post_valid(self):
        """Test registration with valid data"""
        response = self.client.post(reverse('accounts:register'), {
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'username': 'newuser',
            'password1': 'complexpassword123',
            'password2': 'complexpassword123'
        })
        self.assertRedirects(response, reverse('accounts:login'))
        self.assertTrue(User.objects.filter(email='newuser@example.com').exists())

    def test_logout_view(self):
        """Test logout functionality"""
        # Login first
        self.client.login(username='test@example.com', password='testpass123')
        
        # Then logout
        response = self.client.get(reverse('accounts:logout'))
        self.assertRedirects(response, reverse('accounts:login'))

    def test_dashboard_requires_login(self):
        """Test that dashboard requires authentication"""
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={reverse('accounts:dashboard')}")

    def test_dashboard_authenticated_user(self):
        """Test dashboard for authenticated user"""
        self.client.login(username='test@example.com', password='testpass123')
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test User')


class AuthenticationFormsTest(TestCase):
    """Test cases for authentication forms"""
    
    def test_custom_user_creation_form_valid(self):
        """Test CustomUserCreationForm with valid data"""
        form_data = {
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'username': 'testuser',
            'password1': 'complexpassword123',
            'password2': 'complexpassword123'
        }
        form = CustomUserCreationForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_custom_user_creation_form_invalid_email(self):
        """Test CustomUserCreationForm with invalid email"""
        form_data = {
            'email': 'invalid-email',
            'first_name': 'Test',
            'last_name': 'User',
            'username': 'testuser',
            'password1': 'complexpassword123',
            'password2': 'complexpassword123'
        }
        form = CustomUserCreationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_custom_user_creation_form_password_mismatch(self):
        """Test CustomUserCreationForm with password mismatch"""
        form_data = {
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'username': 'testuser',
            'password1': 'complexpassword123',
            'password2': 'differentpassword123'
        }
        form = CustomUserCreationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)

    def test_custom_authentication_form_valid(self):
        """Test CustomAuthenticationForm with valid credentials"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        form_data = {
            'username': 'test@example.com',
            'password': 'testpass123'
        }
        form = CustomAuthenticationForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_custom_authentication_form_invalid(self):
        """Test CustomAuthenticationForm with invalid credentials"""
        form_data = {
            'username': 'test@example.com',
            'password': 'wrongpassword'
        }
        form = CustomAuthenticationForm(data=form_data)
        self.assertFalse(form.is_valid())
