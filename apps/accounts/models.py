"""
User authentication models for HSK Exam System

This module contains the custom user model and related profile models
for managing user accounts and their HSK learning preferences.
"""

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.common.models import TimeStampedModel


class CustomUser(AbstractUser):
    """
    Custom User model extending Django's AbstractUser.
    
    Uses email as the primary authentication field instead of username.
    Includes additional fields for phone number and email verification status.
    """
    
    # Personal Information
    email = models.EmailField(
        unique=True,
        verbose_name='Email',
        help_text='Email address used for login and communications'
    )
    phone_number = models.CharField(
        max_length=20, 
        blank=True, 
        verbose_name='Số điện thoại',
        help_text='Optional phone number for contact'
    )
    
    # Account Status
    is_verified = models.BooleanField(
        default=False, 
        verbose_name='Đã xác thực',
        help_text='Whether the user has verified their email address'
    )

    # Authentication Configuration
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'Người dùng'
        verbose_name_plural = 'Người dùng'
        db_table = 'accounts_customuser'
        ordering = ['last_name', 'first_name']

    def __str__(self):
        """Return a string representation of the user."""
        full_name = self.get_full_name()
        return f"{full_name} ({self.email})" if full_name else self.email

    def get_full_name(self):
        """Return the user's full name."""
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self):
        """Return the user's first name."""
        return self.first_name or self.username

    @property
    def is_profile_complete(self):
        """Check if user has completed their profile setup."""
        if not hasattr(self, 'profile'):
            return False
        profile = self.profile
        return bool(
            profile.date_of_birth and 
            profile.target_hsk_level and 
            profile.chinese_level
        )


class Profile(TimeStampedModel):
    """
    Extended user profile for HSK exam system.
    
    Contains additional information about users including HSK learning preferences,
    study goals, and personal details specific to Chinese language learning.
    """
    
    # User Relationship
    user = models.OneToOneField(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='profile',
        verbose_name='Người dùng'
    )
    
    # Personal Information
    date_of_birth = models.DateField(
        null=True, 
        blank=True, 
        verbose_name='Ngày sinh',
        help_text='Birth date for age-appropriate content and statistics'
    )
    phone_number = models.CharField(
        max_length=20, 
        blank=True, 
        verbose_name='Số điện thoại',
        help_text='Contact phone number'
    )
    bio = models.TextField(
        max_length=500, 
        blank=True,
        verbose_name='Giới thiệu bản thân',
        help_text='Brief introduction about yourself (max 500 characters)'
    )
    avatar = models.ImageField(
        upload_to='avatars/', 
        null=True, 
        blank=True, 
        verbose_name='Ảnh đại diện',
        help_text='Profile picture'
    )

    # Chinese Language Learning Information
    CHINESE_LEVEL_CHOICES = [
        ('beginner', 'Người mới bắt đầu'),
        ('elementary', 'Sơ cấp'),
        ('intermediate', 'Trung cấp'),
        ('advanced', 'Nâng cao'),
    ]
    
    chinese_level = models.CharField(
        max_length=20,
        choices=CHINESE_LEVEL_CHOICES,
        default='beginner',
        verbose_name='Trình độ tiếng Trung hiện tại',
        help_text='Current Chinese language proficiency level'
    )
    
    # HSK Exam Information
    HSK_LEVEL_CHOICES = [(i, f'HSK {i}') for i in range(1, 7)]
    
    target_hsk_level = models.IntegerField(
        choices=HSK_LEVEL_CHOICES,
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(6)],
        verbose_name='Mục tiêu HSK',
        help_text='Target HSK level to achieve'
    )
    study_hours_per_week = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(168)],
        verbose_name='Số giờ học/tuần',
        help_text='Number of study hours per week (0-168)'
    )

    # Location Information
    city = models.CharField(
        max_length=100, 
        blank=True,
        verbose_name='Thành phố',
        help_text='Current city of residence'
    )
    country = models.CharField(
        max_length=100, 
        blank=True, 
        verbose_name='Quốc gia', 
        default='Vietnam',
        help_text='Country of residence'
    )

    # Study Preferences
    STUDY_TIME_CHOICES = [
        ('morning', 'Buổi sáng (6:00 - 12:00)'),
        ('afternoon', 'Buổi chiều (12:00 - 18:00)'),
        ('evening', 'Buổi tối (18:00 - 22:00)'),
        ('night', 'Buổi đêm (22:00 - 6:00)'),
    ]
    
    preferred_study_time = models.CharField(
        max_length=20,
        choices=STUDY_TIME_CHOICES,
        blank=True,
        verbose_name='Thời gian học ưa thích',
        help_text='Preferred time of day for studying'
    )

    class Meta:
        verbose_name = 'Hồ sơ người dùng'
        verbose_name_plural = 'Hồ sơ người dùng'
        db_table = 'accounts_profile'

    def __str__(self):
        """Return string representation of the profile."""
        return f"Hồ sơ của {self.user.get_full_name()}"

    @property
    def age(self):
        """Calculate and return user's age."""
        if not self.date_of_birth:
            return None
        from datetime import date
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )

    @property
    def is_complete(self):
        """Check if profile has all essential information filled."""
        return bool(
            self.date_of_birth and 
            self.chinese_level and 
            self.target_hsk_level and
            self.city and
            self.country
        )

    def get_hsk_level_display_vietnamese(self):
        """Return HSK level formatted for Vietnamese display."""
        return f"HSK {self.target_hsk_level}"

    def get_chinese_level_display_vietnamese(self):
        """Return Chinese level in Vietnamese."""
        level_dict = dict(self.CHINESE_LEVEL_CHOICES)
        return level_dict.get(self.chinese_level, self.chinese_level)
    
    def get_study_time_display_vietnamese(self):
        """Return preferred study time in Vietnamese."""
        if not self.preferred_study_time:
            return 'Chưa thiết lập'
        time_dict = dict(self.STUDY_TIME_CHOICES)
        return time_dict.get(self.preferred_study_time, self.preferred_study_time)

# Signal handlers for automatic profile management
@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Automatically create a profile when a new user is created.
    
    Args:
        sender: The model class (CustomUser)
        instance: The actual instance being saved
        created: Boolean flag indicating if this is a new instance
        **kwargs: Additional keyword arguments
    """
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=CustomUser)
def save_user_profile(sender, instance, **kwargs):
    """
    Automatically save the profile when user is saved.
    
    Args:
        sender: The model class (CustomUser)
        instance: The actual instance being saved
        **kwargs: Additional keyword arguments
    """
    if hasattr(instance, 'profile'):
        instance.profile.save()
