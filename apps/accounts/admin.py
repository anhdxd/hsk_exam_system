from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import CustomUser, Profile


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Admin configuration for CustomUser model"""
    list_display = ('email', 'username', 'first_name',
                    'last_name', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('-date_joined',)

    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'first_name', 'last_name', 'password1', 'password2'),
        }),
    )


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """Admin configuration for Profile model"""
    list_display = ('user', 'chinese_level', 'target_hsk_level',
                    'study_hours_per_week', 'city', 'country')
    list_filter = ('chinese_level', 'target_hsk_level',
                   'country', 'preferred_study_time')
    search_fields = ('user__email', 'user__username',
                     'user__first_name', 'user__last_name', 'city')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        (_('User Information'), {
            'fields': ('user',)
        }),
        (_('Personal Information'), {
            'fields': ('phone_number', 'date_of_birth', 'bio', 'avatar', 'city', 'country')
        }),
        (_('HSK Study Information'), {
            'fields': ('chinese_level', 'target_hsk_level', 'study_hours_per_week', 'preferred_study_time')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
