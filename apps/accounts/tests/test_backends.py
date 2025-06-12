"""
Tests for custom authentication backends
"""

from django.test import TestCase
from django.contrib.auth import authenticate, get_user_model
from apps.accounts.backends import EmailOrUsernameModelBackend

User = get_user_model()


class EmailOrUsernameModelBackendTest(TestCase):
    """Test the EmailOrUsernameModelBackend"""

    def setUp(self):
        self.backend = EmailOrUsernameModelBackend()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User"
        )

    def test_authenticate_with_username(self):
        """Test authentication with username"""
        user = self.backend.authenticate(
            request=None,
            username="testuser",
            password="testpass123"
        )
        self.assertEqual(user, self.user)

    def test_authenticate_with_email(self):
        """Test authentication with email"""
        user = self.backend.authenticate(
            request=None,
            username="test@example.com",
            password="testpass123"
        )
        self.assertEqual(user, self.user)

    def test_authenticate_with_wrong_password(self):
        """Test authentication fails with wrong password"""
        user = self.backend.authenticate(
            request=None,
            username="testuser",
            password="wrongpassword"
        )
        self.assertIsNone(user)

    def test_authenticate_with_nonexistent_user(self):
        """Test authentication fails with nonexistent user"""
        user = self.backend.authenticate(
            request=None,
            username="nonexistent",
            password="testpass123"
        )
        self.assertIsNone(user)

    def test_authenticate_case_insensitive_email(self):
        """Test authentication with case insensitive email"""
        user = self.backend.authenticate(
            request=None,
            username="TEST@EXAMPLE.COM",
            password="testpass123"
        )
        self.assertEqual(user, self.user)

    def test_authenticate_case_insensitive_username(self):
        """Test authentication with case insensitive username"""
        user = self.backend.authenticate(
            request=None,
            username="TESTUSER",
            password="testpass123"
        )
        self.assertEqual(user, self.user)

    def test_authenticate_with_none_username(self):
        """Test authentication fails with None username"""
        user = self.backend.authenticate(
            request=None,
            username=None,
            password="testpass123"
        )
        self.assertIsNone(user)

    def test_authenticate_with_none_password(self):
        """Test authentication fails with None password"""
        user = self.backend.authenticate(
            request=None,
            username="testuser",
            password=None
        )
        self.assertIsNone(user)

    def test_get_user_valid_id(self):
        """Test get_user with valid user ID"""
        user = self.backend.get_user(self.user.pk)
        self.assertEqual(user, self.user)

    def test_get_user_invalid_id(self):
        """Test get_user with invalid user ID"""
        user = self.backend.get_user(99999)
        self.assertIsNone(user)

    def test_django_authenticate_with_username(self):
        """Test Django's authenticate function with username"""
        user = authenticate(username="testuser", password="testpass123")
        self.assertEqual(user, self.user)

    def test_django_authenticate_with_email(self):
        """Test Django's authenticate function with email"""
        user = authenticate(username="test@example.com", password="testpass123")
        self.assertEqual(user, self.user)
