"""
Model tests for HSK Exam System accounts app

Tests for CustomUser and Profile models including:
- Model creation and validation
- Model relationships
- Model methods and properties
- Signal handlers
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from datetime import date, timedelta
from ..models import CustomUser, Profile

User = get_user_model()


class CustomUserModelTest(TestCase):
    """Test cases for CustomUser model"""
    
    def setUp(self):
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'testpass123'
        }

    def test_create_user(self):
        """Test creating a user with valid data"""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.first_name, 'Test')
        self.assertEqual(user.last_name, 'User')
        self.assertTrue(user.check_password('testpass123'))

    def test_user_string_representation(self):
        """Test __str__ method"""
        user = User.objects.create_user(**self.user_data)
        expected = f"Test User ({user.email})"
        self.assertEqual(str(user), expected)

    def test_get_full_name(self):
        """Test get_full_name method"""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.get_full_name(), 'Test User')

    def test_user_default_values(self):
        """Test default values for user fields"""
        user = User.objects.create_user(**self.user_data)
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_verified)


class ProfileModelTest(TestCase):
    """Test cases for Profile model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            first_name='Test',
            last_name='User',
            password='testpass123'
        )

    def test_profile_auto_creation(self):
        """Test that profile is automatically created when user is created"""
        self.assertTrue(hasattr(self.user, 'profile'))
        self.assertIsInstance(self.user.profile, Profile)

    def test_profile_string_representation(self):
        """Test profile __str__ method"""
        expected = f"Hồ sơ của {self.user.get_full_name()}"
        self.assertEqual(str(self.user.profile), expected)
