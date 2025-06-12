"""
Custom authentication backends for HSK Exam System

This module contains custom authentication backends that allow users
to login using either email or username.
"""

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()


class EmailOrUsernameModelBackend(ModelBackend):
    """
    Custom authentication backend that allows users to login with either email or username.
    
    This backend extends Django's default ModelBackend to support multiple
    authentication methods while maintaining security best practices.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate user using email or username.
        
        Args:
            request: The HTTP request object
            username: The username or email provided by user
            password: The password provided by user
            **kwargs: Additional keyword arguments
            
        Returns:
            User instance if authentication successful, None otherwise
        """
        if username is None or password is None:
            return None

        try:
            # Try to find user by email or username
            user = User.objects.get(
                Q(email__iexact=username) | Q(username__iexact=username)
            )
        except User.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a nonexistent user
            User().set_password(password)
            return None

        # Check password and return user if valid
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        
        return None

    def get_user(self, user_id):
        """
        Get user by ID.
        
        Args:
            user_id: The user's primary key
            
        Returns:
            User instance if found, None otherwise
        """
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
        
        return user if self.user_can_authenticate(user) else None
